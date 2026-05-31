from app.src.config.database import Base, engine
from app.src.models.user import User
from app.src.models.persistence import (
    Subject,
    Chapter,
    Topic,
    ChatHistory,
    FormulaHistory,
    SimulationHistory,
    UserSetting,
    UserSession,
)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    main()
