import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Tự động tìm và load các biến từ file .env
load_dotenv()

# Lấy chuỗi kết nối một cách an toàn
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("Lỗi: Không tìm thấy DATABASE_URL trong file .env của Inventory")

# Tạo động cơ kết nối
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo phiên làm việc với Database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class để các file model khác kế thừa
Base = declarative_base()