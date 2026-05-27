from app.src.config.database import Base, engine
from app.src.models.user import User


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    main()
