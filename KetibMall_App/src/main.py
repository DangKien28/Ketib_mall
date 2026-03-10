# File: KetibMall_App/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Đã thêm import này
import os
from src.models import database, models

# Import Router
from src.controllers.product_controller import router as product_router
from src.controllers.order_controller import router as order_router

# 1. KHỞI TẠO APP TRƯỚC (Dòng này phải nằm trên cùng)
app = FastAPI(title="KetibMall App API", version="2.0")

# 2. SAU ĐÓ MỚI CẤU HÌNH MOUNT VÀ MIDDLEWARE
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tự động tạo bảng
models.Base.metadata.create_all(bind=database.engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Server đang chạy với tính năng Upload ảnh!"}

# Đăng ký router
app.include_router(product_router)
app.include_router(order_router)