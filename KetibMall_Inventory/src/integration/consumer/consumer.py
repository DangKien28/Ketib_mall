import pika
import json
import os
from sqlalchemy.orm import Session
from src.models import database, models
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. XỬ LÝ ĐƠN HÀNG MỚI (TRỪ KHO)
# ==========================================
def process_order(ch, method, properties, body):
    data = json.loads(body)
    order_id = data.get("order_id")
    items = data.get("items")
    
    print(f" [v] Đang xử lý xuất kho cho đơn hàng: {order_id}")
    
    db = next(database.get_db())
    try:
        for item in items:
            product_id = item['product_id']
            qty_to_minus = item['quantity']
            
            db_item = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
            if db_item:
                db_item.actual_stock -= qty_to_minus
                new_log = models.InventoryLog(
                    product_id=product_id,
                    change_amount=-qty_to_minus,
                    reason=f"Xuất hàng cho đơn {order_id}"
                )
                db.add(new_log)
        
        db.commit()
        print(f" [OK] Đã cập nhật kho thực cho đơn {order_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f" [!] Lỗi xử lý: {e}")
        db.rollback()

# ==========================================
# 2. XỬ LÝ HỦY ĐƠN HÀNG (SAGA: HOÀN KHO)
# ==========================================
def process_order_cancel(ch, method, properties, body):
    data = json.loads(body)
    order_id = data.get("order_id")
    items = data.get("items")
    
    print(f" [x] Đang xử lý HOÀN KHO cho đơn hàng HỦY: {order_id}")
    
    db = next(database.get_db())
    try:
        for item in items:
            product_id = item['product_id']
            qty_to_add = item['quantity']
            
            # Tìm sản phẩm trong kho thực
            db_item = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
            if db_item:
                # CỘNG LẠI KHO THỰC TẾ
                db_item.actual_stock += qty_to_add
                
                # Ghi log lịch sử nhập kho lại
                new_log = models.InventoryLog(
                    product_id=product_id,
                    change_amount=qty_to_add,
                    reason=f"Hoàn kho do khách hủy đơn {order_id}"
                )
                db.add(new_log)
        
        db.commit()
        print(f" [OK] Đã hoàn lại kho thực cho đơn hủy {order_id}")
        
        # Xác nhận với RabbitMQ là đã xử lý xong
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f" [!] Lỗi xử lý hoàn kho: {e}")
        db.rollback()

# ==========================================
# 3. KHỞI ĐỘNG CÔNG NHÂN LẮNG NGHE
# ==========================================
def start_consuming():
    host = os.getenv("RABBITMQ_HOST")
    user = os.getenv("RABBITMQ_USER")
    password = os.getenv("RABBITMQ_PASS")
    
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
    channel = connection.channel()

    # Khai báo 2 queue để đảm bảo an toàn
    channel.queue_declare(queue='order_queue', durable=True)
    channel.queue_declare(queue='order_cancel_queue', durable=True) # Queue mới

    channel.basic_qos(prefetch_count=1)
    
    # Gắn hàm xử lý cho từng queue tương ứng
    channel.basic_consume(queue='order_queue', on_message_callback=process_order)
    channel.basic_consume(queue='order_cancel_queue', on_message_callback=process_order_cancel)

    print(' [*] Đang chờ tin nhắn từ App. Nhấn Ctrl+C để thoát.')
    channel.start_consuming()

if __name__ == "__main__":
    start_consuming()