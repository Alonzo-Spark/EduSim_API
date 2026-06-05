import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app/src/modules"))

import asyncio
from app.src.modules.tutor.service import analyze_tutor_query

async def main():
    print("Generating response for 'electric current'...")
    res = await analyze_tutor_query(
        query="electric current",
        history=None,
        subject="physics",
        chapter="Electric Current",
        topic="Electric Current",
        student_profile=None
    )
    print("\n=== RAW EXPLANATION ===")
    print(res.get("explanation"))
    print("=======================")

if __name__ == "__main__":
    asyncio.run(main())
