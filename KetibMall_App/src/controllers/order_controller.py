# File: KetibMall_App/src/controllers/order_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from src.models import database, models
from src.schemas import OrderCreate
from src.integration.publisher.publisher import send_order_event

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)

@router.post("/")
def create_order(order: OrderCreate, db: Session = Depends(database.get_db)):
    # 1. Kiểm tra User (Tạo tự động nếu chưa có để test nhanh)
    db_user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not db_user:
        new_user = models.User(id=order.user_id, username=f"User_{order.user_id}", email=f"user{order.user_id}@ketib.com")
        db.add(new_user)
        db.commit()

    # 2. Khởi tạo ID đơn hàng duy nhất
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    new_order = models.Order(id=order_id, user_id=order.user_id, status="PENDING")
    db.add(new_order)

    # Dùng để chứa thông tin gửi sang RabbitMQ
    items_for_mq = []

    # 3. Duyệt danh sách sản phẩm trong đơn hàng
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        # Kiểm tra tồn kho tại chỗ (cached_stock)
        if not product or product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Sản phẩm {item.product_id} không đủ hàng!")
        
        # Trừ kho tạm (cho khách thấy hàng đã giảm ngay lập tức)
        product.cached_stock -= item.quantity
        
        # Lưu chi tiết đơn hàng
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)
        
        # Thêm vào payload gửi đi
        items_for_mq.append({"product_id": item.product_id, "quantity": item.quantity})

    # 4. Lưu vào Database của App
    db.commit()

    # 5. PHÁT TIN NHẮN SANG KHO (RabbitMQ)
    order_payload = {
        "order_id": order_id,
        "items": items_for_mq
    }
    
    try:
        send_order_event(order_payload)
    except Exception as e:
        # Lưu ý: Trong thực tế bạn có thể cần lưu lại log nếu gửi tin thất bại
        print(f"Lỗi gửi tin nhắn: {e}")

    return {
        "message": "Đặt hàng thành công! Đã chuyển thông tin sang hệ thống Kho.",
        "order_id": order_id
    }