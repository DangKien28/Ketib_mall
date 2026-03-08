from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Trỏ vào DB của Kho (Cổng 5433)
SQLALCHEMY_DATABASE_URL = "postgresql://root:Dtk.281005@localhost:5433/ketib_inventory_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()