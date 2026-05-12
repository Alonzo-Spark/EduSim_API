import json
from app.src.modules.simulation_synthesis.service import generate_simulation_synthesis

def test_generation():
    prompt = "Explain me collision using cars as an example"
    
    print(f"Testing Prompt: {prompt}")
    try:
        # This calls the service which uses your updated prompt and validator
        result = generate_simulation_synthesis(prompt)
        
        print("\n✅ GENERATION SUCCESSFUL")
        print(f"Simulation ID: {result['id']}")
        
        # Verify New Structure
        print("\n--- ARCHITECTURE VERIFICATION ---")
        print(f"Has DSL: {'dsl' in result}")
        print(f"Has Knowledge: {'knowledge' in result}")
        print(f"Has Metadata: {'metadata' in result}")

        # Verify DSL
        dsl = result['dsl']
        print("\n--- DSL VERIFICATION ---")
        print(f"Title: {dsl['meta']['title']}")
        print(f"Environment Gravity: {dsl['environment']['gravity']}")
        print(f"Objects Count: {len(dsl['objects'])}")
        print(f"Forces Count: {len(dsl['forces'])}")
        
        # Verify Knowledge
        knowledge = result['knowledge']
        print("\n--- KNOWLEDGE VERIFICATION ---")
        print(f"Formulas: {knowledge['relevant_formulas']}")
        print(f"Explanations: {knowledge['explanations']}")

        # Final check: Save to a local file for you to inspect manually
        with open("v1_test_output.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\nFull output saved to 'v1_test_output.json' for inspection.")

    except Exception as e:
        print(f"\n❌ GENERATION FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()