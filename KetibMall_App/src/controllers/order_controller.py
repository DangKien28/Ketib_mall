from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from src.models import database, models
from src.schemas import OrderCreate
from src.integration.publisher.publisher import send_order_event

# THÊM MỚI: Import trạm kiểm soát Đăng nhập
from src.dependencies import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate, 
    db: Session = Depends(database.get_db),
    # THÊM MỚI: Đặt trạm kiểm soát. Bắt buộc phải có Token hợp lệ.
    current_user: models.User = Depends(get_current_user) 
):
    # CHỈNH SỬA: Không cần kiểm tra User từ order.user_id nữa. 
    # Ta dùng luôn current_user.id được lấy ra một cách an toàn từ Token.

    # 1. Tạo ID đơn hàng
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    
    # Sử dụng current_user.id làm chủ nhân đơn hàng
    new_order = models.Order(id=order_id, user_id=current_user.id, status="PENDING")
    db.add(new_order)

    items_for_mq = []

    # 2. Duyệt sản phẩm
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Sản phẩm {item.product_id} không tồn tại.")
            
        if product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Sản phẩm {product.name} đã hết hàng.")
        
        # Trừ kho tạm trên App
        product.cached_stock -= item.quantity
        
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)
        items_for_mq.append({"product_id": item.product_id, "quantity": item.quantity})

    try:
        db.commit()
        # 3. Gửi tín hiệu sang RabbitMQ cho Inventory
        send_order_event({"order_id": order_id, "items": items_for_mq})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo đơn hàng.")

    return {"message": "Đặt hàng thành công!", "order_id": order_id}