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
        product_id = data.get("product_id")
        new_stock = data.get("new_stock")
        
        print(f" [App] Nhận tín hiệu cập nhật: Sản phẩm {product_id} -> Tồn kho mới: {new_stock}")
        
        # 2. Kết nối Database của App
        # Sử dụng next(get_db()) để lấy session từ generator trong database.py
        db = next(database.get_db())
        
        # 3. Tìm sản phẩm trong DB App để cập nhật cached_stock
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        
        if product:
            product.cached_stock = new_stock
            db.commit()
            print(f" [OK] Đã đồng bộ số lượng cho {product_id} thành công.")
        else:
            print(f" [!] Cảnh báo: Không tìm thấy sản phẩm {product_id} trong database của App.")
            
        # 4. Xác nhận đã xử lý xong tin nhắn
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f" [!] Lỗi khi xử lý tin nhắn đồng bộ kho: {e}")
        # Nếu lỗi, có thể chọn không ack để RabbitMQ gửi lại sau hoặc xử lý tùy nghiệp vụ

def start_stock_consumer():
    """
    Khởi chạy tiến trình lắng nghe RabbitMQ
    """
    # Lấy thông tin cấu hình từ .env
    host = os.getenv("RABBITMQ_HOST")
    user = os.getenv("RABBITMQ_USER")
    password = os.getenv("RABBITMQ_PASS")
    
    try:
        # Thiết lập thông tin đăng nhập
        credentials = pika.PlainCredentials(user, password)
        
        # Kết nối đến RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        channel = connection.channel()

        # Khai báo hàng đợi (phải khớp với tên hàng đợi bên Publisher của Inventory)
        queue_name = 'stock_update_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        # Cấu hình cân bằng tải (mỗi lần chỉ nhận 1 tin nhắn)
        channel.basic_qos(prefetch_count=1)
        
        # Chỉ định hàm xử lý khi có tin nhắn đến
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
    # Để chạy file này: python -m src.integration.stock_consumer
    start_stock_consumer()