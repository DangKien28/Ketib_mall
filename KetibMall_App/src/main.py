from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import pika
import threading
import json
import redis
from src.models import database, models

# Import các router
from src.controllers.cart_controller import router as cart_router
from src.controllers.product_controller import router as product_router
from src.controllers.order_controller import router as order_router
from src.controllers.auth_controller import router as auth_router

app = FastAPI(title="KetibMall App API", version="2.0")

# 1. Cấu hình CORS (Phải liệt kê rõ Origin thay vì dùng "*")
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Cấu hình thư mục static
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Tự động tạo bảng
models.Base.metadata.create_all(bind=database.engine)

# --- CẤU HÌNH REDIS CHO WORKER ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis_cache")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASS = os.getenv("REDIS_PASS")

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASS, decode_responses=True
)

# --- NHÂN VIÊN TRỰC TỔNG ĐÀI RABBITMQ ---
def rabbitmq_worker():
    try:
        RABBITMQ_USERNAME = os.getenv("RABBITMQ_USER")
        RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
        RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
        # Kết nối với Trạm bưu điện RabbitMQ
        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASS)
        
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        
        channel = connection.channel()
        channel.queue_declare(queue='stock_updates') # Lắng nghe hòm thư 'stock_updates'

        # Hành động khi có thư đến
        def callback(ch, method, properties, body):
            data = json.loads(body)
            variant_id = data.get('variant_id')
            new_stock = data.get('stock')

            db = database.SessionLocal()
            try:
                # 1. Sửa số lượng (cached_stock) trong Database App
                variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == variant_id).first()
                if variant:
                    variant.cached_stock = new_stock
                    db.commit()
                    print(f"✅ [RabbitMQ] Đã cập nhật SP {variant_id} thành {new_stock} cái")

                    # 2. XÓA BẢN COPY CŨ TRONG REDIS (Giải quyết lỗi số 1 của bạn!)
                    redis_client.delete("all_products_cache")
                    print("🧹 [RabbitMQ] Đã dọn sạch Tủ lạnh Redis để đồng bộ số lượng!")
            except Exception as e:
                print(f"❌ Lỗi Database Worker: {e}")
            finally:
                db.close()

        print("🐰 [Worker] Đang lắng nghe thư cập nhật Kho từ RabbitMQ...")
        channel.basic_consume(queue='stock_updates', on_message_callback=callback, auto_ack=True)
        channel.start_consuming()
    except Exception as e:
        print(f"❌ RabbitMQ Worker đang chờ hệ thống khởi động... ({e})")

# Bật Nhân viên tổng đài chạy ngầm ngay khi FastAPI khởi động
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=rabbitmq_worker, daemon=True)
    thread.start()


# 4. Đăng ký các router
app.include_router(product_router)
app.include_router(order_router)
app.include_router(auth_router)
app.include_router(cart_router)

@app.get("/")
def home():
    return {"message": "KetibMall System is Online with Auth Support!"}