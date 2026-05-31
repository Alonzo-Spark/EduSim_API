import sys
import os
import uuid

# Setup paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))

from app.src.config.database import SessionLocal
from app.src.models.user import User
from app.src.models.persistence import ChatHistory, FormulaHistory, SimulationHistory
from app.src.services.persistence_service import (
    save_tutor_conversation,
    record_formula_calculation,
    save_sandbox_state,
    save_formula_explanation_to_chat_history,
)


def test_db_operations():
    db = SessionLocal()
    try:
        # 1. Fetch user (e.g. admin or any user)
        user = db.query(User).first()
        if not user:
            print("No users found. Registering a test user...")
            from app.src.utils.auth import hash_password

            user = User(
                name="Test Student",
                email="student@edusim.local",
                password_hash=hash_password("StudentPass123!"),
                role="student",
                is_email_verified=True,
                is_mobile_verified=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        print(f"Testing with user: {user.email}")

        # 2. Test Tutor Conversation save
        print("Testing Tutor Conversation...")
        payload = {
            "source_query": "What is acceleration?",
            "explanation": "Acceleration is the rate of change of velocity.",
            "topic": "acceleration",
            "subject": "physics",
        }
        conv = save_tutor_conversation(db, user=user, payload=payload)
        db.commit()
        print(f"Saved tutor conversation. Session ID: {conv.id}")

        # Verify saved in chat_history
        chats = db.query(ChatHistory).filter(ChatHistory.session_id == conv.id).all()
        assert len(chats) >= 1, "Tutor chat messages not saved!"
        print(f"Verified tutor chat history count: {len(chats)}")

        # 3. Test Formula Explanation save
        print("Testing Formula Explanation...")

        class MockRes:
            title = "Newton's Second Law"
            description = "F=ma"
            purpose = "Calculate Force"
            applications = ["Rocket lift off"]
            common_mistakes = ["Not converting mass to kg"]

        save_formula_explanation_to_chat_history(db, user, "F=ma", MockRes())
        db.commit()
        print("Saved formula explanation to chat history.")

        # Verify in chat_history
        formula_chats = db.query(ChatHistory).filter(ChatHistory.session_type == "formula_lab").all()
        assert len(formula_chats) >= 2, "Formula explanation not saved!"
        print(f"Verified formula explanation history count: {len(formula_chats)}")

        # 4. Test Formula Calculation save
        print("Testing Formula Calculation...")
        calc_payload = {
            "session_id": str(uuid.uuid4()),
            "formula_id": "F=ma",
            "input_json": {"m": 10, "a": 9.8},
            "output_json": {"F": 98.0},
        }
        calc = record_formula_calculation(db, user=user, payload=calc_payload)
        db.commit()
        print(f"Saved formula calculation. ID: {calc.id}")

        # Verify in formula_history
        calcs = db.query(FormulaHistory).filter(FormulaHistory.id == calc.id).all()
        assert len(calcs) == 1, "Formula calculation not saved!"
        print(f"Verified formula calculation history count: {len(calcs)}")

        # 5. Test Sandbox/Simulation state save
        print("Testing Sandbox State...")
        sim_payload = {
            "simulation_id": "sim-test-123",
            "prompt": "Drop a ball",
            "title": "Ball Drop Test",
        }
        sim = save_sandbox_state(db, user=user, payload=sim_payload)
        db.commit()
        print(f"Saved sandbox simulation. ID: {sim.id}")

        # Verify in simulation_history
        sims = db.query(SimulationHistory).filter(SimulationHistory.id == sim.id).all()
        assert len(sims) == 1, "Simulation history not saved!"
        print(f"Verified simulation history count: {len(sims)}")

        print("\n=== ALL DATABASE REFACTOR TESTS COMPLETED SUCCESSFULLY! ===")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_db_operations()
