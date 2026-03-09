import pika
import json
import os
from sqlalchemy.orm import Session
from src.models import database, models
from dotenv import load_dotenv

load_dotenv()

def process_order(ch, method, properties, body):
    # 1. Giải mã tin nhắn JSON nhận được từ App
    data = json.loads(body)
    order_id = data.get("order_id")
    items = data.get("items")
    
    print(f" [v] Đang xử lý đơn hàng: {order_id}")
    
    # 2. Kết nối Database của Inventory
    db = next(database.get_db())
    
    try:
        for item in items:
            product_id = item['product_id']
            qty_to_minus = item['quantity']
            
            # Tìm sản phẩm trong kho thực
            db_item = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
            
            if db_item:
                # Trừ kho thực tế
                db_item.actual_stock -= qty_to_minus
                
                # Ghi log lịch sử xuất kho
                new_log = models.InventoryLog(
                    product_id=product_id,
                    change_amount=-qty_to_minus,
                    reason=f"Xuất hàng cho đơn {order_id}"
                )
                db.add(new_log)
        
        db.commit()
        print(f" [OK] Đã cập nhật kho thực cho đơn {order_id}")
        
        # Xác nhận với RabbitMQ là đã xử lý xong để xóa tin nhắn khỏi hàng đợi
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f" [!] Lỗi xử lý: {e}")
        db.rollback()

def start_consuming():
    # Lấy thông tin từ .env
    host = os.getenv("RABBITMQ_HOST")
    user = os.getenv("RABBITMQ_USER")
    password = os.getenv("RABBITMQ_PASS")
    
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
    channel = connection.channel()

    # Khai báo lại queue để đảm bảo an toàn
    channel.queue_declare(queue='order_queue', durable=True)

    # Cấu hình để mỗi lần chỉ xử lý 1 tin nhắn (không bị quá tải)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='order_queue', on_message_callback=process_order)

    print(' [*] Đang chờ tin nhắn từ App. Nhấn Ctrl+C để thoát.')
    channel.start_consuming()

if __name__ == "__main__":
    start_consuming()