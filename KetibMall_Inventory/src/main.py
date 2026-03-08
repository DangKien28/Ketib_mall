# File: KetibMall_App_Inventory/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.models import database, models
from src.controllers.inventory_controller import router as inventory_router

app = FastAPI(title="KetibMall Inventory API", version="1.0")

# Tự động tạo bảng inventory và inventory_logs trong Database
models.Base.metadata.create_all(bind=database.engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Inventory Service is running", "service": "KetibMall_Inventory"}

# Đăng ký router nhập/xuất kho
app.include_router(inventory_router)