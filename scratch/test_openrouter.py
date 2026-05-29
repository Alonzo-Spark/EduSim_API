import asyncio
import sys
import os

# Add parent directories to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.src.modules.legacy_rag.generator import generate_llm_text_async, generate_llm_text

async def main():
    print("Testing generate_llm_text...")
    try:
        res = generate_llm_text("Hello, tell me a 1-word greeting.", temperature=0.1)
        print("Sync response:", res)
    except Exception as e:
        print("Sync error:", e)

    print("Testing generate_llm_text_async...")
    try:
        res_async = await generate_llm_text_async("Hello, tell me a 1-word greeting.", temperature=0.1)
        print("Async response:", res_async)
    except Exception as e:
        print("Async error:", e)

if __name__ == "__main__":
    asyncio.run(main())
