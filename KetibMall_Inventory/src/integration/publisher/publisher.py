import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

def send_stock_update(product_id: str, new_stock: int):
    host = os.getenv("RABBITMQ_HOST")
    user = os.getenv("RABBITMQ_USER")
    password = os.getenv("RABBITMQ_PASS")
    
    try:
        credentials = pika.PlainCredentials(user, password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        channel = connection.channel()

        # Tạo hàng đợi mới chuyên cho việc cập nhật kho
        queue_name = 'stock_update_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        message = json.dumps({"product_id": product_id, "new_stock": new_stock})
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        print(f" [Inventory] Đã báo cập nhật kho SP: {product_id} -> {new_stock}")
    except Exception as e:
        print(f" [!] Lỗi gửi cập nhật kho: {e}")