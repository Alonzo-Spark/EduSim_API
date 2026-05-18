"""
scratch/test_sandbox_engine.py
==============================
Definitive next-generation Developer CLI script for the EduSim Sandbox Engine.

Demonstrates the entire stateful physical pipeline in memory:
1. Contextual textbook RAG lookup + dynamic LLM prompt synthesis (or offline fallback).
2. Dynamic physical shape compilation & unit normalisation via SandboxInitializer.
3. authoratative RuntimeStore hydration and pre-evaluation of direct/derived observables.
4. Dynamic widget parameter mutation (updating mass in real-time & observing kinetic energy shift).
5. Chronological snapshot checkpointing, coordinate warping, and stateful restoration.
"""

import sys
import os
import json
import time

# Configure absolute paths for standalone execution
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))

from app.src.modules.sandbox import service
from app.src.modules.sandbox.serializers import RuntimeSerializer


def run_sandbox_engine_demo():
    print("=" * 80)
    print("      🚀 EDUSIM STATEFUL PHYSICS SANDBOX ENGINE CLI BENCHMARK 🚀      ")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # STEP 1: Sandbox Initialization & Hydration
    # -------------------------------------------------------------------------
    prompt = "Sexplain collision using cars"
    print(f"\n👉 STEP 1: Spawning Stateful Simulation Session...")
    print(f"   Prompt: '{prompt}'")
    
    start_time = time.time()
    result = service.generate_simulation(prompt=prompt)
    duration = time.time() - start_time
    
    simulation_id = result["simulation_id"]
    payload = result["payload"]
    
    print(f"✅ Stateful Sandbox Initialized successfully in {duration:.2f}s!")
    print(f"   Simulation UUID: {simulation_id}")
    
    metadata = payload["metadata"]
    ai_ctx = metadata.get("ai_context", {})
    print(f"   Scenario Title:  '{ai_ctx.get('scenario_name', 'Untitled Scenario')}'")
    print(f"   Curriculum Tags: {ai_ctx.get('curriculum_topics', [])}")
    
    # Save payload to JSON file for developer inspection
    output_path = "scratch/test_sandbox_payload.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"💾 Generated physical payload saved to: {output_path}")
    
    # -------------------------------------------------------------------------
    # STEP 2: Inspecting Hydrated Sandbox Parameters
    # -------------------------------------------------------------------------
    print(f"\n👉 STEP 2: Inspecting Authoritative Serializer Payload...")
    
    objects = payload["objects"]
    print(f"\n📦 Compiled Physical Objects ({len(objects)}):")
    for obj in objects:
        pos = obj["physics"]["position"]
        phys = obj["physics"]
        print(f"  - Object '{obj['id']}': Mass={phys['mass']} kg, Position=({pos['x']}, {pos['y']}), Velocity=({phys['velocity']['x']}, {phys['velocity']['y']})")
        
    controls = payload["controls"]
    print(f"\n🎛️ Active Interactive Controls ({len(controls)}):")
    for ctrl in controls:
        binding = ctrl["binding"]
        config = ctrl.get("widget_config", {})
        print(f"  - Control '{ctrl['id']}' [{ctrl['widget_type']}]: Binding={binding.get('scope')}.{binding.get('property_path')} | Range=[{config.get('min_value', 'N/A')}, {config.get('max_value', 'N/A')}]")
        
    observables = payload["observables"]
    print(f"\n📊 Reactive Observables Clocks ({len(observables)}):")
    for obs in observables:
        print(f"  - Observable '{obs['id']}': Value={obs['value']} {obs.get('unit', '')} | Mode={obs['display'].get('display_mode')}")
        
    relationships = payload["relationships"]
    print(f"\n📐 Textbook Educational Relationships ({len(relationships)}):")
    for rel in relationships:
        print(f"  - '{rel['name']}': Formula={rel['formula_latex']}")
        
    # -------------------------------------------------------------------------
    # STEP 3: Real-Time Parameter Mutations & Recalculation
    # -------------------------------------------------------------------------
    print(f"\n👉 STEP 3: Simulating Real-Time Widget Interactivity (Parameter Mutation)...")
    
    # Find a dynamic object to modify mass for (e.g. first object)
    if objects:
        target_obj = objects[0]
        target_id = target_obj["id"]
        old_mass = target_obj["physics"]["mass"]
        
        # We will dynamically inject a mass control widget if not present, and update
        print(f"   Attempting to update the mass of '{target_id}'...")
        print(f"   Original Mass: {old_mass} kg")
        
        # Trigger dynamic service control update
        # Let's bind a control to this object
        store = service._active_sessions[simulation_id]
        from app.src.modules.sandbox.schemas import SandboxControl, ControlBinding
        
        dummy_control = SandboxControl(
            id="dynamic_mass_slider",
            label="Dynamic Mass",
            widget_type="slider",
            binding=ControlBinding(
                scope="object",
                object_id=target_id,
                property_path="physics.mass"
            ),
            widget_config={
                "min_value": 0.1,
                "max_value": 100.0,
                "step": 0.1,
                "default_value": old_mass
            }
        )
        store.schema.controls.append(dummy_control)
        
        # Apply the mutation using the dynamic control service API
        updated_result = service.update_control(
            simulation_id=simulation_id,
            control_id="dynamic_mass_slider",
            value=25.0
        )
        
        updated_payload = updated_result["payload"]
        updated_obj = [o for o in updated_payload["objects"] if o["id"] == target_id][0]
        new_mass = updated_obj["physics"]["mass"]
        
        print(f"🔥 MUTATION APPLIED SUCCESSFULLY via Service Controller!")
        print(f"   New Dynamic Mass: {new_mass} kg")
        assert new_mass == 25.0, "Mutation was not correctly applied to PhysicsState!"
        
    # -------------------------------------------------------------------------
    # STEP 4: Chronological State Capture and Undo/Redo Restores
    # -------------------------------------------------------------------------
    print(f"\n👉 STEP 4: Capture & Restoring Sandbox Checkpoint Timelines...")
    
    # 1. Take snapshot of current state
    snapshot_response = service.get_snapshot(simulation_id=simulation_id)
    snapshot_checkpoint = snapshot_response["snapshot"]
    print("📸 Deep-serializable snapshot of frame 0 successfully generated!")
    
    # 2. Warp object positions in memory
    store = service._active_sessions[simulation_id]
    if store.objects:
        obj_to_warp = list(store.objects.values())[0]
        original_x = obj_to_warp.position.x
        obj_to_warp.position.x = 999.0
        print(f"   Warped '{obj_to_warp.id}' coordinate x: {original_x} ➡️ {obj_to_warp.position.x}")
        
    # 3. Restore snapshot to roll-back the warp
    restore_response = service.restore_snapshot(
        simulation_id=simulation_id,
        snapshot_data=snapshot_checkpoint
    )
    
    restored_payload = restore_response["payload"]
    restored_obj = restored_payload["objects"][0]
    restored_x = restored_obj["physics"]["position"]["x"]
    print(f"⏳ Restored Session Snapshot to roll-back changes...")
    print(f"   Restored '{restored_obj['id']}' coordinate x: {restored_x}")
    
    assert restored_x == original_x, "Snapshot restoration failed to recover coordinates!"
    print("🎉 Snapshot Recovery Verification: 100% PERFECT SUCCESS!")
    
    print("\n" + "=" * 80)
    print("      🎉 ALL NEXT-GEN EDUSIM STATEFUL SANDBOX ENGINE CHECKS PASSED!      ")
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_sandbox_engine_demo()
    except Exception as e:
        print(f"\n❌ STATEFUL ENGINE FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
