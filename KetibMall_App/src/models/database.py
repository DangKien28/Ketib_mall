# File: KetibMall_App/src/models/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Format: postgresql://[user]:[password]@localhost:[port]/[database_name]
SQLALCHEMY_DATABASE_URL = "postgresql://root:Dtk.281005@localhost:5432/ketib_app_db"

# Tạo động cơ kết nối
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo phiên làm việc với Database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class để các file model khác kế thừa
Base = declarative_base()