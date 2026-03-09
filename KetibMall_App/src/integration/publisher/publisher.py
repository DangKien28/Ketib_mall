# File: KetibMall_App/src/integration/publisher.py
import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

def send_order_event(order_payload: dict):
    # Load lại môi trường
    load_dotenv() 

    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_user = os.getenv("RABBITMQ_USER") # Sẽ lấy 'KetibAdmin'
    rabbitmq_pass = os.getenv("RABBITMQ_PASS")
    
    try:
        # 1. Thiết lập kết nối đến RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host)
        )
        channel = connection.channel()

        # 2. Khai báo hàng đợi (Queue) - durable=True để tin nhắn không mất khi restart
        queue_name = 'order_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        # 3. Chuyển dict sang chuỗi JSON và gửi đi
        message = json.dumps(order_payload)
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
            )
        )
        
        print(f" [AMQP] Đã gửi thông tin đơn hàng {order_payload['order_id']} sang RabbitMQ")
        connection.close()
        
    except Exception as e:
        print(f" [!] Lỗi khi kết nối RabbitMQ: {e}")