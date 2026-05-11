import json
from app.src.modules.simulation_synthesis.service import generate_simulation_synthesis

def test_generation():
    prompt = "A 10kg iron ball falling from 50 meters with air resistance. Add a slider for mass."
    
    print(f"Testing Prompt: {prompt}")
    try:
        # This calls the service which uses your updated prompt and validator
        result = generate_simulation_synthesis(prompt)
        
        print("\n✅ GENERATION SUCCESSFUL")
        print(f"Simulation Title: {result['title']}")
        print(f"Simulation ID: {result['id']}")
        
        # Verify the structure of the DSL
        dsl = result['dsl']
        print("\n--- DSL VERIFICATION ---")
        print(f"Meta ID: {dsl['meta']['id']}")
        print(f"Environment Gravity: {dsl['environment']['gravity']}")
        print(f"Interactions Count: {len(dsl['interactions'])}")
        
        if len(dsl['interactions']) > 0:
            print(f"First Binding Path: {dsl['interactions'][0]['bind']}")

        # Final check: Save to a local file for you to inspect manually
        with open("v1_test_output.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\nFull output saved to 'v1_test_output.json' for inspection.")

    except Exception as e:
        print(f"\n❌ GENERATION FAILED")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_generation()