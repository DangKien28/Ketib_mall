import pika
import json
import os
import sys
import redis
from sqlalchemy.orm import Session
from src.models import database, models
from dotenv import load_dotenv

load_dotenv()

# --- CẤU HÌNH REDIS ---
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_PASS = os.getenv("REDIS_PASS")

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASS, decode_responses=True
)

def update_app_stock(ch, method, properties, body):
    try:
        data = json.loads(body)
        variant_id = data.get("variant_id") or data.get("product_id")
        new_stock = data.get("new_stock")
        
        print(f" [App] Nhận tín hiệu cập nhật: Biến thể {variant_id} -> Tồn kho mới: {new_stock}")
        db = next(database.get_db())
        
        # Tìm và cập nhật Database App
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == variant_id).first()
        if variant:
            variant.cached_stock = new_stock 
            db.commit()
            print(f" [OK] Đã đồng bộ số lượng cho {variant_id} thành công.")
            
            # --- DỌN TỦ LẠNH REDIS TẠI ĐÂY ---
            redis_client.delete("all_products_cache")
            print(" 🧹 [Redis] Đã dọn sạch Cache để Web hiển thị số mới!")
        else:
            print(f" [!] Cảnh báo: Không tìm thấy biến thể {variant_id} trong database App.")
            
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f" [!] Lỗi khi xử lý tin nhắn đồng bộ kho: {e}")
        db.rollback()

def start_stock_consumer():
    host = os.getenv("RABBITMQ_HOST")
    user = os.getenv("RABBITMQ_USER")
    password = os.getenv("RABBITMQ_PASS")
    
    try:
        credentials = pika.PlainCredentials(user, password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        channel = connection.channel()

        queue_name = 'stock_update_queue'
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=update_app_stock)

        print(' [*] APP CONSUMER: Đang chờ tín hiệu cập nhật kho từ Inventory...')
        channel.start_consuming()

    except Exception as e:
        print(f" [!] Lỗi hệ thống: {e}")

if __name__ == "__main__":
    start_stock_consumer()