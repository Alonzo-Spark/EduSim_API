"""
mutations.py
============
Controlled State Mutations for the EduSim Runtime Store.

All live sandbox state updates must flow exclusively through mutations. 
This guarantees transactional safety, defensive validation, caching flushes, 
reactive evaluations, and notifications for subscribers.
"""

from __future__ import annotations

from typing import Any, Optional, Dict
from app.src.modules.sandbox.state.runtime_store import RuntimeStore
from app.src.modules.sandbox.state.object_state import ObjectRuntimeState, StateVector2D
from app.src.modules.sandbox.schemas.object_schema import SandboxObject, ShapeType, PhysicsProperties, VisualHints, RuntimeMetadata
from app.src.modules.sandbox.schemas.constaraint_schema import SandboxConstraint


def pause_simulation(store: RuntimeStore) -> None:
    """Halts execution clock."""
    store.simulation.pause()
    store.notify()


def resume_simulation(store: RuntimeStore) -> None:
    """Starts execution clock."""
    store.simulation.resume()
    store.notify()


def update_mass(store: RuntimeStore, object_id: str, new_mass: float) -> None:
    """
    Mutates body mass.
    Triggers caching flushes, derived educational observable recalculations,
    and dispatches live notifications to external observers.
    """
    obj = store.objects.get(object_id)
    if not obj:
        raise ValueError(f"Target object '{object_id}' not found for mass update.")

    # Defensive validation
    validated_mass = max(0.001, float(new_mass))
    
    # 1. Update Object State
    obj.mass = validated_mass
    
    # Update inertia proportionally (fallback calculation cylinder)
    if obj.inertia > 0.0:
        obj.inertia = (obj.inertia / (obj.mass if obj.mass > 0 else 1.0)) * validated_mass

    # Update in schema to remain synced
    schema_obj = next((o for o in store.schema.objects if o.id == object_id), None)
    if schema_obj:
        schema_obj.physics.mass = validated_mass

    # 2. Invalidate caching & evaluate derived observable chains (reactive recomputation)
    store.observables.invalidate_cache()
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)

    # 3. Dispatch changes to frontend synchronization & subscribers
    store.notify()


def apply_force(store: RuntimeStore, object_id: str, fx: float, fy: float) -> None:
    """
    Applies translational force to a dynamic physical body.
    Increments net force vectors and updates dynamic acceleration components.
    """
    obj = store.objects.get(object_id)
    if not obj:
        return

    if obj.is_static:
        return

    # Increment forces
    obj.net_force.x += float(fx)
    obj.net_force.y += float(fy)

    # Recompute immediate linear acceleration (a = F / m)
    obj.acceleration.x = obj.net_force.x / obj.mass
    obj.acceleration.y = obj.net_force.y / obj.mass

    # Invalidate caching & evaluate observables
    store.observables.invalidate_cache()
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)
    store.notify()


def update_velocity(store: RuntimeStore, object_id: str, vx: float, vy: float) -> None:
    """Directly alters physical body speed parameters."""
    obj = store.objects.get(object_id)
    if not obj or obj.is_static:
        return

    obj.velocity.x = float(vx)
    obj.velocity.y = float(vy)

    # Invalidate caching & evaluate observables
    store.observables.invalidate_cache()
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)
    store.notify()


def set_position(store: RuntimeStore, object_id: str, x: float, y: float) -> None:
    """Teleports body coordinates to designated locations."""
    obj = store.objects.get(object_id)
    if not obj:
        return

    obj.position.x = float(x)
    obj.position.y = float(y)

    # Keep schema synced
    schema_obj = next((o for o in store.schema.objects if o.id == object_id), None)
    if schema_obj:
        schema_obj.position.x = float(x)
        schema_obj.position.y = float(y)

    # Invalidate caching & evaluate observables
    store.observables.invalidate_cache()
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)
    store.notify()


def select_object_mutation(store: RuntimeStore, object_id: Optional[str]) -> None:
    """Alters focus targets and resets highlight states."""
    # Deselect previous selection
    prev_id = store.interaction.selected_object_id
    if prev_id:
        prev_obj = store.objects.get(prev_id)
        if prev_obj:
            prev_obj.is_selected = False

    # Select new object
    store.interaction.select_object(object_id)
    if object_id:
        obj = store.objects.get(object_id)
        if obj:
            obj.is_selected = True

    store.notify()


def update_widget_mutation(store: RuntimeStore, control_id: str, value: Any) -> None:
    """Alters UI slider selection values and propagates to mapped bindings."""
    store.interaction.update_widget(control_id, value)

    # Traverse bindings to locate destination schemas
    control_schema = next((c for c in store.schema.controls if c.id == control_id), None)
    if control_schema and control_schema.binding:
        binding = control_schema.binding
        
        # Apply to specific object parameters
        if binding.scope == "object" and binding.object_id:
            if "mass" in str(binding.property_path).lower():
                update_mass(store, binding.object_id, float(value))
            elif "velocity" in str(binding.property_path).lower() or "vel" in str(binding.property_path).lower():
                # Direct speed update
                obj = store.objects.get(binding.object_id)
                if obj:
                    update_velocity(store, binding.object_id, float(value), obj.velocity.y)
        
        # Apply to global environment fields
        elif binding.scope == "environment":
            if "gravity" in str(binding.property_path).lower():
                store.schema.environment.gravity.y = float(value)
                
                # Invalidate and propagate
                store.observables.invalidate_cache()
                g_y = store.get_gravity_y()
                store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)
                store.notify()


# ===========================================================================
# Lightweight Sandbox Dynamic Editing mutations API
# ===========================================================================

def add_object(store: RuntimeStore, obj_schema: SandboxObject) -> ObjectRuntimeState:
    """
    Dynamically registers and spawns a new physical object in the sandbox.
    Keeps store runtime index and base SandboxSchema in sync.
    """
    # 1. Validation
    if obj_schema.id in store.objects:
        raise ValueError(f"An object with ID '{obj_schema.id}' already exists in the sandbox.")
        
    if obj_schema.physics.mass <= 0:
        raise ValueError("Cannot add an object with non-positive mass.")

    # 2. Append to underlying schema objects array
    store.schema.objects.append(obj_schema)

    # 3. Calculate Moment of Inertia
    inertia = 1.0
    if obj_schema.radius is not None:
        inertia = 0.5 * obj_schema.physics.mass * (obj_schema.radius ** 2)
    elif obj_schema.width is not None and obj_schema.height is not None:
        inertia = (1.0 / 12.0) * obj_schema.physics.mass * (obj_schema.width**2 + obj_schema.height**2)

    # 4. Instantiate runtime state representation
    v = obj_schema.runtime.initial_velocity
    p = obj_schema.position
    
    state = ObjectRuntimeState(
        id=obj_schema.id,
        position=StateVector2D(x=p.x, y=p.y),
        velocity=StateVector2D(x=v.x, y=v.y),
        acceleration=StateVector2D(x=0.0, y=0.0),
        angle=obj_schema.runtime.initial_angle,
        angular_velocity=obj_schema.runtime.initial_angular_vel,
        mass=obj_schema.physics.mass,
        inertia=inertia,
        is_static=obj_schema.is_static,
        is_sleeping=obj_schema.runtime.is_sleeping,
        is_sensor=obj_schema.physics.is_sensor,
        is_visible=obj_schema.visuals.visible
    )
    
    # 5. Populate in lookup map
    store.objects[obj_schema.id] = state

    # 6. Invalidate observables cache and evaluate reactive variables
    store.observables.invalidate_cache()
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)

    # 7. Notify observers of new object addition
    store.notify()
    return state


def remove_object(store: RuntimeStore, object_id: str) -> None:
    """
    Deletes an object from the runtime environment.
    Removes connected constraints, clears pointers, and triggers recomputation.
    """
    if object_id not in store.objects:
        return

    # 1. Remove associated joint constraints anchoring this body
    linked_constraints = [
        cid for cid, c in store.constraints.items()
        if c.anchor_a.body_id == object_id or c.anchor_b.body_id == object_id
    ]
    for cid in linked_constraints:
        remove_constraint(store, cid)

    # 2. Reset selection/hover states if references match deleted body
    if store.interaction.selected_object_id == object_id:
        store.interaction.selected_object_id = None
    if store.interaction.hovered_object_id == object_id:
        store.interaction.hovered_object_id = None
    if store.interaction.dragged_object_id == object_id:
        store.interaction.dragged_object_id = None

    # 3. Evict from indices
    del store.objects[object_id]
    store.schema.objects = [o for o in store.schema.objects if o.id != object_id]

    # 4. Invalidate and evaluate
    store.observables.invalidate_cache()
    g_y = store.get_gravity_y()
    store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)

    # 5. Notify subscribers
    store.notify()


def update_object(store: RuntimeStore, object_id: str, updates: Dict[str, Any]) -> None:
    """
    Updates live physics, visual, or runtime characteristics of an object.
    Automatically keeps schema records aligned and handles secondary variables (like inertia).
    """
    obj = store.objects.get(object_id)
    schema_obj = next((o for o in store.schema.objects if o.id == object_id), None)
    if not obj or not schema_obj:
        return

    # Invalidate observables once if any field changes
    any_changed = False

    # Extract update keys and propagate
    for k, v in updates.items():
        if k == "mass":
            update_mass(store, object_id, float(v))
            any_changed = True
        elif k in ("position", "pos"):
            set_position(store, object_id, float(v["x"]), float(v["y"]))
            any_changed = True
        elif k in ("velocity", "vel"):
            update_velocity(store, object_id, float(v["x"]), float(v["y"]))
            any_changed = True
        elif k == "is_static":
            val = bool(v)
            obj.is_static = val
            schema_obj.is_static = val
            any_changed = True
        elif k == "radius":
            val = float(v)
            schema_obj.radius = val
            obj.inertia = 0.5 * obj.mass * (val ** 2)
            any_changed = True
        elif k in ("is_visible", "visible"):
            val = bool(v)
            obj.is_visible = val
            schema_obj.visuals.visible = val
        elif k in ("color", "style_color"):
            schema_obj.visuals.color = str(v)
        elif k == "restitution":
            schema_obj.physics.restitution = float(v)
        elif k == "friction":
            schema_obj.physics.friction = float(v)
        elif k == "air_resistance":
            schema_obj.runtime.air_resistance = float(v)
            any_changed = True
        elif k == "is_dragged":
            obj.is_dragged = bool(v)
        elif k == "angle":
            obj.angle = float(v)
            any_changed = True
        elif k == "angular_velocity":
            obj.angular_velocity = float(v)
            any_changed = True
        elif k == "runtime_flags":
            obj.runtime_flags.update(dict(v))

    if any_changed:
        store.observables.invalidate_cache()
        g_y = store.get_gravity_y()
        store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)
        
    store.notify()


def add_constraint(store: RuntimeStore, constraint: SandboxConstraint) -> SandboxConstraint:
    """
    Registers a new joint, spring, or rope constraint between bodies or fixed coordinates.
    """
    if constraint.id in store.constraints:
        raise ValueError(f"Constraint ID '{constraint.id}' already exists.")

    # Validate anchor object targets exist
    if constraint.anchor_a.body_id and constraint.anchor_a.body_id not in store.objects:
        raise ValueError(f"Anchor A targeting missing object '{constraint.anchor_a.body_id}'")
    if constraint.anchor_b.body_id and constraint.anchor_b.body_id not in store.objects:
        raise ValueError(f"Anchor B targeting missing object '{constraint.anchor_b.body_id}'")

    # Add to schema and registry
    if not store.schema.constraints:
        store.schema.constraints = []
    store.schema.constraints.append(constraint)
    store.constraints[constraint.id] = constraint

    store.notify()
    return constraint


def remove_constraint(store: RuntimeStore, constraint_id: str) -> None:
    """
    Evicts a physical constraint from the sandbox system.
    """
    if constraint_id not in store.constraints:
        return

    del store.constraints[constraint_id]
    if store.schema.constraints:
        store.schema.constraints = [c for c in store.schema.constraints if c.id != constraint_id]

    store.notify()


def update_environment(store: RuntimeStore, updates: Dict[str, Any]) -> None:
    """
    Updates environmental characteristics of the active scene (gravity vectors, atmosphere drag).
    """
    env = store.schema.environment
    any_changed = False

    for k, v in updates.items():
        if k == "gravity.y":
            env.gravity.y = float(v)
            any_changed = True
        elif k == "gravity.x":
            env.gravity.x = float(v)
            any_changed = True
        elif k == "gravity.scale":
            env.gravity.scale = float(v)
            any_changed = True
        elif k == "air_density":
            env.atmosphere.air_density = float(v)
            any_changed = True
        elif k == "wind.magnitude":
            if env.wind:
                env.wind.magnitude = float(v)
                any_changed = True
        elif k == "wind.direction_deg":
            if env.wind:
                env.wind.direction_deg = float(v)
                any_changed = True

    if any_changed:
        store.observables.invalidate_cache()
        g_y = store.get_gravity_y()
        store.observables.evaluate_all(store.objects, g_y, store.simulation.frame_count)
        
    store.notify()
