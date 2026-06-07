import json
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Setup app search path for sandbox execution
root_dir = os.getcwd()
sys.path.append(os.path.join(root_dir, "app", "src"))
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))

from app.src.modules.sandbox.service import generate_simulation

def test_v3_generation():
    # Scenario: Friction and Motion with Assets
    prompt = "create a visually rich simulation of a block on a table to explain inertia. use a wooden block asset if possible. add sliders for mass and force."
    
    print(f"--- NEXT-GEN EDUSIM SANDBOX COMPILATION TEST ---")
    print(f"Prompt: {prompt}")
    
    try:
        result = generate_simulation(prompt)
        payload = result['payload']
        
        print("\n✅ METADATA CHECK:")
        ai_ctx = payload['metadata'].get('ai_context', {})
        print(f"Title: {ai_ctx.get('scenario_name', 'Untitled Scenario')}")
        print(f"Topic: {ai_ctx.get('curriculum_topics', [])}")
        
        print("\n✅ OBJECTS CHECK:")
        for obj in payload['objects']:
            label = obj['display'].get('label', obj['id'])
            mass = obj['physics'].get('mass', 'N/A')
            asset_info = "No Asset"
            if 'visual_hints' in obj and obj['visual_hints'].get('asset_id'):
                asset_info = f"Asset: {obj['visual_hints'].get('asset_id')}"
            print(f"- {label}: Mass={mass}kg, {asset_info}, Shape={obj.get('shape')}")
            
        print("\n✅ CONTROLS CHECK (Parameters):")
        for p in payload['controls']:
            print(f"- UI Widget: {p['label']} | Binding Scope: {p['binding'].get('scope')}")
 
        print("\n✅ OBSERVABLES CHECK:")
        for o in payload['observables']:
            unit = o.get('unit', '')
            print(f"- Monitoring: {o['id']} (Unit: {unit})")
 
        print("\n✅ EDUCATIONAL RELATIONSHIPS CHECK:")
        for r in payload.get('relationships', []):
            print(f"- Concept: {r.get('name', 'Unknown')} | Formula: {r.get('latex_formula')}")

        # Save result for inspection
        with open("v3_test_output.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\nSUCCESS: Output saved to v3_test_output.json")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        # Print traceback for debugging
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_v3_generation()
