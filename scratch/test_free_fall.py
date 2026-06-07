"""
test_free_fall.py
=================
Unit test to verify the FreeFallPrimitive generator correctness,
making sure the generated payloads completely pass Pydantic schema validation.
"""

import sys
import os

# Adjust path to import correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.primitives.mechanics.gravity.free_fall import FreeFallPrimitive
from app.src.modules.sandbox.schemas import SandboxSchema


def test_free_fall_primitive_default():
    print("Testing FreeFallPrimitive defaults...")
    primitive = FreeFallPrimitive()
    schema = primitive.build()
    
    # Assert type is SandboxSchema
    assert isinstance(schema, SandboxSchema)
    
    # Assert objects are correct
    object_ids = {obj.id for obj in schema.objects}
    assert "falling_body" in object_ids
    assert "ground" in object_ids
    
    # Assert environmental gravity is correct
    assert schema.environment.gravity.y == 1.0
    
    # Assert controls are bound correctly
    control_ids = {ctrl.id for ctrl in schema.controls}
    assert "gravity_slider" in control_ids
    assert "mass_slider" in control_ids
    assert "init_velocity_slider" in control_ids
    assert "air_resistance_slider" in control_ids
    
    # Assert observables exist
    obs_ids = {obs.id for obs in schema.observables}
    assert "vel_obs" in obs_ids
    assert "accel_obs" in obs_ids
    assert "height_obs" in obs_ids
    assert "ke_obs" in obs_ids
    assert "pe_obs" in obs_ids
    assert "fg_obs" in obs_ids
    
    # Assert educational relationships are added
    rel_ids = {rel.id for rel in schema.relationships}
    assert "newton_2nd_law_fall" in rel_ids
    assert "gravity_accel_relationship" in rel_ids
    assert "mass_independence" in rel_ids
    assert "energy_conservation_fall" in rel_ids
    
    print("SUCCESS: Default FreeFallPrimitive successfully built and validated!")


def test_free_fall_primitive_custom():
    print("Testing FreeFallPrimitive with custom parameters...")
    primitive = FreeFallPrimitive(
        mass=5.5,
        radius=25.0,
        initial_height=500.0,
        initial_velocity=10.0,
        gravity_strength=1.62,  # Moon gravity
        restitution=0.8,
        air_resistance=0.0
    )
    schema = primitive.build()
    
    # Validate customized properties
    falling_body = next(o for o in schema.objects if o.id == "falling_body")
    assert falling_body.physics.mass == 5.5
    assert falling_body.radius == 25.0
    assert falling_body.physics.restitution == 0.8
    assert falling_body.runtime.initial_velocity.y == 10.0
    assert falling_body.runtime.air_resistance == 0.0
    
    assert schema.environment.gravity.y == 1.62
    assert schema.environment.atmosphere.air_density == 0.0
    
    print("SUCCESS: Custom FreeFallPrimitive successfully built and validated!")


if __name__ == "__main__":
    test_free_fall_primitive_default()
    test_free_fall_primitive_custom()
    print("All tests passed successfully!")
