from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from src.models import database, models
from src.schemas import OrderCreate
from src.integration.publisher.publisher import send_order_event

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(database.get_db)):
    # 1. Kiểm tra User có tồn tại thực sự không
    db_user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User không hợp lệ. Vui lòng đăng nhập lại."
        )

    # 2. Tạo ID đơn hàng
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    new_order = models.Order(id=order_id, user_id=order.user_id, status="PENDING")
    db.add(new_order)

    items_for_mq = []

    # 3. Duyệt sản phẩm
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
        # 4. Gửi tín hiệu sang RabbitMQ cho Inventory
        send_order_event({"order_id": order_id, "items": items_for_mq})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo đơn hàng.")

    return {"message": "Đặt hàng thành công!", "order_id": order_id}