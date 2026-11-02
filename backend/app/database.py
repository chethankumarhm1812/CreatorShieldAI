from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate_schema():
    tables = set(inspect(engine).get_table_names())
    migrations = {
        "evidence": ("verified_amount", "FLOAT NOT NULL DEFAULT 0"),
        "incidents": ("exclusion_code", "VARCHAR(80)"),
    }
    for table, (column_name, column_type) in migrations.items():
        if table not in tables:
            continue
        columns = {column["name"] for column in inspect(engine).get_columns(table)}
        if column_name not in columns:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}"))
