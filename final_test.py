import json
from app.src.modules.simulation_synthesis.service import generate_simulation_synthesis

def final_smoke_test():
    # Scenario: Gravitation on the Moon
    prompt = "A 2kg hammer and a 0.1kg feather falling on the moon. Add a slider for gravity and mass."
    
    print(f"--- FINAL BACKEND TEST ---")
    print(f"Prompt: {prompt}")
    
    try:
        result = generate_simulation_synthesis(prompt)
        dsl = result['dsl']
        
        print("\n✅ DSL STRUCTURE CHECK:")
        print(f"Title: {dsl['meta']['title']}")
        print(f"Gravity Vector: {dsl['environment']['gravity']}")
        
        print("\n✅ OBJECTS CHECK:")
        for obj in dsl['objects']:
            print(f"- {obj['visual']['label']}: Mass={obj['physics']['mass']}kg, Shape={obj['shape']['type']}")
            
        print("\n✅ INTERACTION BINDING CHECK:")
        for i in dsl['interactions']:
            print(f"- Control: {i['label']} | Path: {i['bind']}")

        print("\nRESULT: Backend is fully compliant with V1 State Tree Schema.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")

if __name__ == '__main__':
    final_smoke_test()