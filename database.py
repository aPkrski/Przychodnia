from pathlib import Path

from sqlalchemy import create_engine, inspect, Column, String, Numeric, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "poradnie.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def migrate_invoices_table():
    """Ensure invoices table has category and company_name columns."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('invoices')] if 'invoices' in inspector.get_table_names() else []
    
    if 'invoices' in inspector.get_table_names():
        if 'category' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN category VARCHAR(120) DEFAULT ''"))
                conn.commit()
        if 'company_name' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN company_name VARCHAR(140) DEFAULT ''"))
                conn.commit()


def migrate_clinics_table():
    """Ensure clinics table has number column for proper sorting."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('clinics')] if 'clinics' in inspector.get_table_names() else []
    
    if 'clinics' in inspector.get_table_names():
        if 'number' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE clinics ADD COLUMN number INTEGER DEFAULT 0"))
                conn.commit()


def init_db():
    from models import Clinic, Location

    Base.metadata.create_all(engine)
    
    # Migrate invoices table to add new columns if needed
    migrate_invoices_table()
    migrate_clinics_table()
    
    with SessionLocal() as session:
        if session.query(Location).count() == 0:
            locations = ["Żyrardów", "Pruszków"]
            for name in locations:
                location = Location(name=name)
                session.add(location)
                session.flush()
                for index in range(1, 12):
                    clinic = Clinic(name=f"Poradnia {index}", location_id=location.id, number=index)
                    session.add(clinic)
            session.commit()
        else:
            # Update clinic numbers if they're not set
            clinics = session.query(Clinic).filter(Clinic.number == 0).all()
            for clinic in clinics:
                # Extract number from name "Poradnia X"
                try:
                    num = int(clinic.name.split()[-1])
                    clinic.number = num
                except (ValueError, IndexError):
                    clinic.number = 0
            if clinics:
                session.commit()
