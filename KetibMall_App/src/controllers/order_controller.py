# File: KetibMall_App/src/controllers/order_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from src.models import database, models
from src.schemas import OrderCreate

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)

@router.post("/")
def create_order(order: OrderCreate, db: Session = Depends(database.get_db)):
    # Tạo user mẫu nếu chưa có
    db_user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not db_user:
        new_user = models.User(id=order.user_id, username="Khach Hang Test", email="test@ketib.com")
        db.add(new_user)
        db.commit()

    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    new_order = models.Order(id=order_id, user_id=order.user_id, status="PENDING")
    db.add(new_order)

    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product or product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail="Sản phẩm không đủ hàng hoặc không tồn tại!")
        
        product.cached_stock -= item.quantity
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)

    db.commit()
    return {"message": "Đặt hàng thành công!", "order_id": order_id}