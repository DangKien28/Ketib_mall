import pika
import json
import os
import sys
from sqlalchemy.orm import Session
from src.models import database, models
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def update_app_stock(ch, method, properties, body):
    """
    Hàm xử lý khi nhận được tin nhắn cập nhật kho từ Inventory
    """
    try:
        # 1. Giải mã dữ liệu JSON
        data = json.loads(body)
        
        # Lấy variant_id (Hỗ trợ cả key cũ product_id đề phòng publisher bên kia chưa đổi tên key)
        variant_id = data.get("variant_id") or data.get("product_id")
        new_stock = data.get("new_stock")
        
        print(f" [App] Nhận tín hiệu cập nhật: Biến thể {variant_id} -> Tồn kho mới: {new_stock}")
        
        # 2. Kết nối Database của App
        db = next(database.get_db())
        
        # 3. TÌM TRONG BẢNG ProductVariant THAY VÌ Product
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == variant_id).first()
        
        if variant:
            variant.cached_stock = new_stock # Cập nhật kho tạm cho biến thể
            db.commit()
            print(f" [OK] Đã đồng bộ số lượng cho {variant_id} thành công.")
        else:
            print(f" [!] Cảnh báo: Không tìm thấy biến thể {variant_id} trong database của App.")
            
        # 4. Xác nhận đã xử lý xong tin nhắn
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f" [!] Lỗi khi xử lý tin nhắn đồng bộ kho: {e}")
        db.rollback()

def start_stock_consumer():
    """
    Khởi chạy tiến trình lắng nghe RabbitMQ
    """
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
        print(' [*] Nhấn Ctrl+C để dừng.')
        
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print(" [!] Không thể kết nối đến RabbitMQ. Hãy kiểm tra Docker.")
    except KeyboardInterrupt:
        print(" [!] Đang dừng Consumer...")
        sys.exit(0)
    except Exception as e:
        print(f" [!] Lỗi hệ thống: {e}")

if __name__ == "__main__":
    start_stock_consumer()