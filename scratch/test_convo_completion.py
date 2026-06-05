import asyncio
import uuid
from app.src.config.database import SessionLocal
from app.src.models.persistence import ChatHistory
from app.src.modules.legacy_rag.generator import generate_openrouter_text_async, _is_response_complete, get_tutor_prompt, NEW_RENDERING_SYSTEM

async def run_trace():
    db = SessionLocal()
    try:
        # Load the history from session 50d97c63-c4e2-43de-9116-1b63ec5acd34
        # up to index 4 (so it includes the user question and assistant answer before 'give formula for it')
        sid = uuid.UUID("50d97c63-c4e2-43de-9116-1b63ec5acd34")
        chats = db.query(ChatHistory).filter(ChatHistory.session_id == sid).order_by(ChatHistory.created_at.asc()).all()
        
        # We want the first 5 messages (indices 0 to 4)
        history = [{"role": c.role, "content": c.content} for c in chats[:5]]
        print(f"Loaded history length: {len(history)}")
        for idx, h in enumerate(history):
            print(f"  {idx}: {h['role']} -> {repr(h['content'][:60])}")
            
        # The query is 'give formula for it'
        query = "give formula for it"
        
        # Let's get the context and prompt
        context = "" # No context for fallback mode
        prompt = get_tutor_prompt(context, query, fallback_mode=True)
        
        print("\n--- Generating response with trace ---")
        # Call generate_openrouter_text_async
        res = await generate_openrouter_text_async(
            prompt,
            temperature=0.3,
            max_output_tokens=2500,
            system_prompt=NEW_RENDERING_SYSTEM,
            history=history
        )
        
        print("\n--- Raw Response ---")
        print(res)
        print("--------------------")
        
        is_complete = _is_response_complete(res, prompt=prompt, system_prompt=NEW_RENDERING_SYSTEM, history=history)
        print(f"\nResponse length: {len(res)}")
        print(f"Ends with: {repr(res[-10:]) if res else 'None'}")
        print(f"Is response complete according to validator: {is_complete}")
        
    finally:
        db.close()

asyncio.run(run_trace())
