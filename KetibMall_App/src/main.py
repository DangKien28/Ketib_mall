# File: KetibMall_App/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.models import database, models

# Import Router từ 2 file riêng biệt
from src.controllers.product_controller import router as product_router
from src.controllers.order_controller import router as order_router

app = FastAPI(title="KetibMall App API", version="2.0")

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
    return {"message": "Server đang chạy với kiến trúc đa Controller!"}

# Đăng ký 2 router vào hệ thống
app.include_router(product_router)
app.include_router(order_router)