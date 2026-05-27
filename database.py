from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "poradnie.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def init_db():
    from models import Clinic, Location

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.query(Location).count() == 0:
            locations = ["Żyrardów", "Pruszków"]
            for name in locations:
                location = Location(name=name)
                session.add(location)
                session.flush()
                for index in range(1, 12):
                    clinic = Clinic(name=f"Poradnia {index}", location_id=location.id)
                    session.add(clinic)
            session.commit()
