import asyncio
import sys
import os

# Add parent directories to sys.path like main.py
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))
sys.path.append(os.path.join(root_dir, "app", "src"))

from app.src.modules.tutor.service import analyze_tutor_query

async def main():
    print("Testing analyze_tutor_query with a pendulum query...")
    try:
        res = await analyze_tutor_query("How do I build a simple pendulum in the sandbox?")
        print("\n--- RESPONSE KEYS ---")
        print(res.keys())
        
        print("\n--- SIMULATION GUIDE ---")
        guide = res.get("simulation_guide", {})
        print("Is Buildable:", guide.get("is_buildable"))
        print("Title:", guide.get("title"))
        
        steps = guide.get("steps", [])
        print(f"Steps Count: {len(steps)}")
        for step in steps[:2]:
            print(f"Step {step.get('step_number')}: {step.get('title')} -> {step.get('description')[:100]}...")
            
        print("\n--- SPAWN CONFIG ---")
        spawn_config = guide.get("spawn_config", {})
        print("Spawn Config Keys:", spawn_config.keys())
        print("Bodies count:", len(spawn_config.get("bodies", [])))
        print("Constraints count:", len(spawn_config.get("constraints", [])))
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
