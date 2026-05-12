from app.src.modules.simulation_synthesis.service import generate_simulation_synthesis
import json
import os

def test_generation(prompt, filename="v1_test_output.json"):
    print(f"\nTesting Prompt: {prompt}")
    try:
        result = generate_simulation_synthesis(prompt)
        
        # Verify absence of deprecated fields
        def check_deprecated(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k in ["movable", "groundFriction"]:
                        raise ValueError(f"CRITICAL: Found deprecated field '{k}'")
                    check_deprecated(v)
            elif isinstance(d, list):
                for item in d:
                    check_deprecated(item)

        check_deprecated(result)
        
        print("\n✅ GENERATION SUCCESSFUL")
        print(f"Simulation ID: {result.get('id')}")
        
        # DSL structure check
        dsl = result.get("dsl", {})
        print("\n--- ARCHITECTURE VERIFICATION ---")
        print(f"Has DSL: {'dsl' in result}")
        print(f"Has Knowledge: {'knowledge' in result}")
        print(f"Has Metadata: {'metadata' in result}")
        
        print("\n--- DSL VERIFICATION ---")
        print(f"Title: {dsl.get('meta', {}).get('title')}")
        print(f"Environment Gravity: {dsl.get('environment', {}).get('gravity')}")
        print(f"Objects Count: {len(dsl.get('objects', []))}")
        print(f"Constraints Count: {len(dsl.get('constraints', []))}")
        
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
            
        return True
    except Exception as e:
        print(f"\n❌ GENERATION FAILED")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    prompts = [
        "Explain me pendulum motion",
        "Rocket propulsion and gravitation",
        "Car collision on a road"
    ]
    
    for i, p in enumerate(prompts):
        test_generation(p, f"v1_test_{i}.json")