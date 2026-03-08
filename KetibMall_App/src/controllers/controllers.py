from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from src.models import database, models
from src.schemas import ProductCreate, OrderCreate

# Khởi tạo Router
router = APIRouter()

# --- API SẢN PHẨM ---
@router.get("/api/products", tags=["Products"])
def get_products(db: Session = Depends(database.get_db)):
    return db.query(models.Product).all()

@router.post("/api/products", tags=["Products"])
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product.id).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Mã sản phẩm đã tồn tại!")
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Thêm thành công", "data": new_product}

# --- API ĐẶT HÀNG ---
@router.post("/api/orders", tags=["Orders"])
def create_order(order: OrderCreate, db: Session = Depends(database.get_db)):
    # Tạo user mẫu
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
            raise HTTPException(status_code=400, detail="Sản phẩm không tồn tại hoặc hết hàng!")
        
        product.cached_stock -= item.quantity
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)

    db.commit()
    return {"message": "Đặt hàng thành công!", "order_id": order_id}