import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

def send_order_event(order_payload: dict):
    load_dotenv() 

    rabbitmq_host = os.getenv("RABBITMQ_HOST")
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS")
    
    try:
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        # 1. Thiết lập kết nối đến RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
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

# ==========================================
# THÊM MỚI: HÀM GỬI TÍN HIỆU HỦY ĐƠN (SAGA)
# ==========================================
def send_order_cancel_event(cancel_payload: dict):
    load_dotenv() 

    rabbitmq_host = os.getenv("RABBITMQ_HOST")
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS")
    
    try:
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
        )
        channel = connection.channel()
        
        # Khai báo một hàng đợi MỚI chuyên dùng để Hủy đơn
        queue_name = 'order_cancel_queue'
        channel.queue_declare(queue=queue_name, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(cancel_payload),
            properties=pika.BasicProperties(
                delivery_mode=2, # Giúp tin nhắn không bị mất nếu RabbitMQ sập
            ) 
        )
        
        print(f" [AMQP] Đã gửi tín hiệu HỦY đơn hàng {cancel_payload['order_id']} sang RabbitMQ")
        connection.close()
        
    except Exception as e:
        print(f" [!] Lỗi khi phát tín hiệu hủy đơn: {e}")