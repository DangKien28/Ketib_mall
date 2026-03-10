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
    # 1. Kiểm tra User có tồn tại thực sự trong DB hay không
    db_user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=404, 
            detail="Người dùng không hợp lệ hoặc phiên làm việc đã hết hạn. Vui lòng đăng nhập lại."
        )

    # 2. Khởi tạo ID đơn hàng duy nhất
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    new_order = models.Order(id=order_id, user_id=order.user_id, status="PENDING")
    db.add(new_order)

    items_for_mq = []

    # 3. Duyệt danh sách sản phẩm trong đơn hàng
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        # Kiểm tra tồn kho tại chỗ (cached_stock)
        if not product or product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Sản phẩm {item.product_id} không đủ hàng hoặc không tồn tại!")
        
        # Trừ kho tạm thời trên App Service
        product.cached_stock -= item.quantity
        
        # Lưu chi tiết đơn hàng
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)
        
        items_for_mq.append({"product_id": item.product_id, "quantity": item.quantity})

    # 4. Lưu vào Database
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi xử lý đơn hàng.")

    # 5. Gửi sự kiện sang RabbitMQ để dịch vụ Inventory xử lý kho thực tế
    order_payload = {
        "order_id": order_id,
        "items": items_for_mq
    }
    
    try:
        send_order_event(order_payload)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn đồng bộ kho: {e}")

    return {
        "message": "Đặt hàng thành công!",
        "order_id": order_id,
        "customer": db_user.full_name
    }