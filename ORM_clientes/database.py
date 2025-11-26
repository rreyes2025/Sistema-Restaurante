from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# nombre de la base de datos SQLite
DATABASE_URL = "sqlite:///restaurant.db"

# crear motor con check same thread = False para evitar errores con la GUI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()