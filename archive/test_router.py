import asyncio
from app.src.routers.educational_router import EducationalRequest
from app.src.rag.engine import rag_engine

async def main():
    try:
        res = await rag_engine.process_topic_request("projectile_motion")
        print(res)
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()

asyncio.run(main())
