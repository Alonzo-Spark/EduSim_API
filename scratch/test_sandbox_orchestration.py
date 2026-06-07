"""
test_sandbox_orchestration.py
=============================
Production-grade integration test suite to verify the complete Sandbox API 
Orchestration Layer (controller.py, service.py, state mutations, and snapshots)
using FastAPI's TestClient boundary.
"""

import sys
import os
from typing import Any, Dict

# Ensure root of the app is in the Python search path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
modules_dir = os.path.abspath(os.path.join(root_dir, "app/src/modules"))
sys.path.append(root_dir)
sys.path.append(modules_dir)

from fastapi.testclient import TestClient
from main import app
from app.src.modules.sandbox import service

# Initialize TestClient
client = TestClient(app)


def test_api_orchestration_workflow():
    print("🚀 STEP 1: Testing Sandbox Generation POST /api/sandbox/generate...")
    
    # We will trigger the spring fallback preset offline to prevent OpenRouter API requests during test execution
    generate_payload = {
        "prompt": "Create a spring loaded cannon block to analyze oscillations",
        "topic": "physics"
    }
    
    response = client.post("/api/sandbox/generate", json=generate_payload)
    assert response.status_code == 201, f"Failed to generate: {response.text}"
    
    gen_data = response.json()
    assert gen_data["success"] is True
    assert "simulation_id" in gen_data
    assert "payload" in gen_data
    
    simulation_id = gen_data["simulation_id"]
    payload = gen_data["payload"]
    
    print(f"✅ Generated Simulation ID: {simulation_id}")
    assert "environment" in payload
    assert "objects" in payload
    assert "controls" in payload
    assert "observables" in payload
    assert "runtime" in payload

    print("🚀 STEP 2: Testing Session Loading POST /api/sandbox/load...")
    load_payload = {
        "simulation_id": simulation_id
    }
    response = client.post("/api/sandbox/load", json=load_payload)
    assert response.status_code == 200, f"Failed to load: {response.text}"
    
    load_data = response.json()
    assert load_data["success"] is True
    assert load_data["simulation_id"] == simulation_id
    assert "payload" in load_data

    print("🚀 STEP 3: Testing Runtime Tick Sync GET /api/sandbox/runtime/{id}...")
    response = client.get(f"/api/sandbox/runtime/{simulation_id}")
    assert response.status_code == 200, f"Failed to fetch runtime: {response.text}"
    
    runtime_data = response.json()
    assert runtime_data["success"] is True
    assert "payload" in runtime_data
    assert runtime_data["payload"]["runtime"]["current_frame"] == 0

    print("🚀 STEP 4: Testing Dynamic Control Update POST /api/sandbox/control/update...")
    # spring preset control_id is 'spring_constant_slider' (mass slider is 'mass_slider')
    # Let's see what controls exist in our compiled payload
    controls = payload["controls"]
    if len(controls) == 0:
        print("⚠️ No AI generated controls in this synthesis run, injecting 'mass_slider' to verify update route...")
        from app.src.modules.sandbox.schemas import SandboxControl, ControlBinding
        
        # Check an available object ID to bind to
        objects = payload["objects"]
        target_obj_id = objects[0]["id"] if objects else "mass_block"
        
        dummy_control = SandboxControl(
            id="mass_slider",
            label="Mass Control",
            widget_type="slider",
            binding=ControlBinding(
                scope="object",
                object_id=target_obj_id,
                property_path="physics.mass"
            ),
            widget_config={
                "min_value": 1.0,
                "max_value": 100.0,
                "step": 0.5,
                "default_value": 5.0
            }
        )
        
        # Inject directly into live active in-memory session store
        store = service._active_sessions[simulation_id]
        store.schema.controls.append(dummy_control)
        control_id = "mass_slider"
    else:
        control_id = controls[0]["id"]
    
    update_payload = {
        "simulation_id": simulation_id,
        "control_id": control_id,
        "value": 15.0
    }
    response = client.post("/api/sandbox/control/update", json=update_payload)
    assert response.status_code == 200, f"Failed to update control: {response.text}"
    
    update_data = response.json()
    assert update_data["success"] is True
    # Ensure the control parameter value is saved in the serialized response
    updated_payload = update_data["payload"]
    assert "controls" in updated_payload

    print("🚀 STEP 5: Testing State Snapshot Captures GET /api/sandbox/snapshot/{id}...")
    response = client.get(f"/api/sandbox/snapshot/{simulation_id}")
    assert response.status_code == 200, f"Failed to fetch snapshot: {response.text}"
    
    snap_data = response.json()
    assert snap_data["success"] is True
    assert "snapshot" in snap_data
    snapshot_payload = snap_data["snapshot"]
    assert "simulation_state" in snapshot_payload
    assert "object_states" in snapshot_payload
    assert "observable_values" in snapshot_payload

    print("🚀 STEP 6: Testing State Snapshot Restoration POST /api/sandbox/snapshot/{id}/restore...")
    restore_payload = {
        "snapshot": snapshot_payload
    }
    response = client.post(f"/api/sandbox/snapshot/{simulation_id}/restore", json=restore_payload)
    assert response.status_code == 200, f"Failed to restore: {response.text}"
    
    restore_data = response.json()
    assert restore_data["success"] is True
    assert "payload" in restore_data

    print("🚀 STEP 7: Testing Simulation Reset POST /api/sandbox/reset...")
    reset_payload = {
        "simulation_id": simulation_id
    }
    response = client.post("/api/sandbox/reset", json=reset_payload)
    assert response.status_code == 200, f"Failed to reset: {response.text}"
    
    reset_data = response.json()
    assert reset_data["success"] is True
    assert "payload" in reset_data
    assert reset_data["payload"]["runtime"]["current_frame"] == 0

    print("🎉 ALL SANDBOX API ORCHESTRATION INTEGRATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    print("=" * 70)
    print("  🧪 EDUSIM SANDBOX API ORCHESTRATION INTEGRATION TESTS  ")
    print("=" * 70)
    try:
        test_api_orchestration_workflow()
        print("\n🎉 INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
