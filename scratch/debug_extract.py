import asyncio
import os
import sys

# Setup paths to match main.py
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))
sys.path.append(os.path.join(root_dir, "app", "src"))

from app.src.modules.legacy_rag import vector_store
from services.rag_service import RagService
from services.formula_service import FormulaService

async def test_full_pipeline():
    # Load vector store
    vector_store.load_all()
    
    query = "friction"
    chunks = RagService.search_chunks("physics", "", query)
    text = "\n\n".join([c["text"] for c in chunks])
    
    print("\n--- FIRST PIPELINE RUN (Cache Miss expected) ---")
    res1 = await FormulaService.extract_formulas(text, query)
    print("Extracted formulas count:", len(res1.get("formulas", [])))
    
    if res1.get("formulas"):
        first_formula = res1["formulas"][0]["formula"]
        print(f"Fetching details for formula: '{first_formula}'...")
        details1 = await FormulaService.get_formula_details(first_formula)
        print("Details title:", details1.title)
        
    print("\n--- SECOND PIPELINE RUN (Cache Hit expected) ---")
    res2 = await FormulaService.extract_formulas(text, query)
    print("Extracted formulas count:", len(res2.get("formulas", [])))
    
    if res2.get("formulas"):
        first_formula = res2["formulas"][0]["formula"]
        print(f"Fetching details for formula: '{first_formula}'...")
        details2 = await FormulaService.get_formula_details(first_formula)
        print("Details title:", details2.title)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
