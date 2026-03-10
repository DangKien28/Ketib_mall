from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from src.models import database, models

# 1. Import các router
from src.controllers.product_controller import router as product_router
from src.controllers.order_controller import router as order_router
from src.controllers.auth_controller import router as auth_router

app = FastAPI(title="KetibMall App API", version="2.0")

# Cấu hình thư mục static
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tự động tạo bảng trong Database
models.Base.metadata.create_all(bind=database.engine)

# Cấu hình CORS (Cho phép Frontend truy cập)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500", # Cổng của Live Server bạn đang dùng
        "http://localhost:5500",
        "*"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Đăng ký các router vào ứng dụng
app.include_router(product_router)
app.include_router(order_router)
app.include_router(auth_router)

@app.get("/")
def home():
    return {"message": "KetibMall System is Online with Auth Support!"}