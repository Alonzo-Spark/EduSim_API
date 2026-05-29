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
    print("Testing analyze_tutor_query and writing output to UTF-8 file...")
    try:
        res = await analyze_tutor_query("What is Newton's Second Law?")
        explanation = res.get("ai_explanation", "")
        
        output_file = os.path.join(root_dir, "scratch", "explanation_output.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(explanation)
            
        print("Successfully wrote explanation to:", output_file)
        print("Does 'Important Notes' appear in the text?", "Important Notes" in explanation)
        print("Does 'Introduction' appear?", "Introduction" in explanation)
        print("Does 'Characteristics' appear?", "Characteristics" in explanation)
        print("Does 'Formula' appear?", "Formula" in explanation)
        print("Does 'Example' appear?", "Example" in explanation)
        print("Does 'Applications' appear?", "Applications" in explanation)
        print("Does 'Summary' appear?", "Summary" in explanation)
        print("Does 'Suggested Questions' appear?", "Suggested Questions" in explanation)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
