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
    print("Testing analyze_tutor_query with a sample prompt...")
    try:
        res = await analyze_tutor_query("What is Newton's Second Law?")
        print("Tutor Query Response keys:", res.keys())
        print("Response title:", res.get("title"))
        print("Response formula:", res.get("formula"))
        print("Response related concepts:", res.get("related_concepts"))
        print("Response concepts:", res.get("concepts"))
        print("Response formulas:", res.get("formulas"))
        print("Response ai_explanation length:", len(res.get("ai_explanation", "")))
        print("Response ai_explanation (snippet):", res.get("ai_explanation", "")[:300])
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
