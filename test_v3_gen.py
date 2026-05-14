import json
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.src.modules.simulation_synthesis.service import generate_simulation_synthesis

def test_v3_generation():
    # Scenario: Friction and Motion with Assets
    prompt = "create a visually rich simulation of a block on a table to explain inertia. use a wooden block asset if possible. add sliders for mass and force."
    
    print(f"--- EDU-SIM DSL V3.0 GENERATION TEST ---")
    print(f"Prompt: {prompt}")
    
    try:
        result = generate_simulation_synthesis(prompt)
        dsl = result['dsl']
        
        print("\n✅ META CHECK:")
        print(f"Title: {dsl['meta']['title']}")
        print(f"Version: {dsl['meta']['version']}")
        
        print("\n✅ OBJECTS CHECK:")
        for obj in dsl['objects']:
            label = obj['visual'].get('label', obj['id'])
            mass = obj['physics'].get('mass', 'N/A')
            asset_info = "No Asset"
            if 'asset' in obj['visual'] and obj['visual']['asset'].get('enabled'):
                asset_info = f"Asset: {obj['visual']['asset'].get('assetId')}"
            print(f"- {label}: Mass={mass}kg, {asset_info}, Category={obj.get('category')}, BodyType={obj.get('bodyType')}")
            
        print("\n✅ CONTROLS CHECK (Parameters):")
        for p in dsl['controls']['parameters']:
            print(f"- Slider: {p['label']} | Bind: {p['bind']}")
            
        print("\n✅ CONTROLS CHECK (Actions):")
        for a in dsl['controls']['actions']:
            print(f"- Button: {a['label']} | Action: {a['action']}")

        print("\n✅ OBSERVABLES CHECK:")
        for o in dsl['observables']:
            unit = o.get('unit', '')
            precision = o.get('precision', 'N/A')
            print(f"- Monitoring: {o['label']} (Unit: {unit}, Precision: {precision})")

        print("\n✅ FORMULA BINDINGS:")
        for f in dsl.get('formulaBindings', []):
            print(f"- Formula: {f.get('formula', f.get('id', 'Unknown'))}")

        print("\n✅ INTERACTIONS CHECK:")
        for i in dsl.get('interactions', []):
            print(f"- Interaction: {i['type']} on targets {i.get('targets', [])}")

        print("\n✅ EVENTS CHECK:")
        for e in dsl.get('events', []):
            print(f"- Event: {e['type']} on targets {e.get('targets', [])}")

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
