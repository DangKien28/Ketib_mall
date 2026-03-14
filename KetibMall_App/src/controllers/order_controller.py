from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from src.models import database, models
from src import schemas
from src.dependencies import get_current_user, get_admin_user

# Import cả 2 hàm publisher
from src.integration.publisher.publisher import send_order_event, send_order_cancel_event

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# ==========================================
# 1. KHÁCH HÀNG ĐẶT HÀNG
# ==========================================
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user) 
):
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    new_order = models.Order(id=order_id, user_id=current_user.id, status="PENDING")
    db.add(new_order)

    items_for_mq = []

    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Sản phẩm {item.product_id} không tồn tại.")
            
        if product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Sản phẩm {product.name} đã hết hàng.")
        
        product.cached_stock -= item.quantity
        
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)
        items_for_mq.append({"product_id": item.product_id, "quantity": item.quantity})

    try:
        db.commit()
        send_order_event({"order_id": order_id, "items": items_for_mq})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo đơn hàng.")

    return {"message": "Đặt hàng thành công!", "order_id": order_id}

# ==========================================
# 2. ADMIN XEM DANH SÁCH ĐƠN HÀNG
# ==========================================
@router.get("/")
def get_all_orders(
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    
    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "user_id": o.user_id,
            "status": o.status,
            "items_count": len(o.items)
        })
    return result

# ==========================================
# 3. ADMIN CẬP NHẬT TRẠNG THÁI (CÓ SAGA PATTERN)
# ==========================================
@router.put("/{order_id}/status")
def update_order_status(
    order_id: str,
    status_data: schemas.OrderStatusUpdate,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    # 1. Tìm đơn hàng
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
    
    valid_statuses = ["PENDING", "PAID", "SHIPPING", "COMPLETED", "CANCELED"]
    if status_data.status not in valid_statuses:
         raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")

    # 2. LOGIC SAGA: HOÀN KHO KHI HỦY ĐƠN
    # (Chỉ thực hiện nếu trạng thái mới là CANCELED và trạng thái hiện tại chưa phải CANCELED)
    if status_data.status == "CANCELED" and order.status != "CANCELED":
        items_for_mq = []
        
        # Duyệt qua từng sản phẩm trong đơn hàng để hoàn lại số lượng vào kho tạm
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.cached_stock += item.quantity
            
            # Lưu lại thông tin để gửi sang Inventory
            items_for_mq.append({"product_id": item.product_id, "quantity": item.quantity})
        
        try:
            # Cập nhật trạng thái và lưu Database
            order.status = status_data.status
            db.commit()
            
            # Gửi loa thông báo sang RabbitMQ
            send_order_cancel_event({"order_id": order_id, "items": items_for_mq})
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi hủy đơn hàng.")
            
    else:
        # Nếu chỉ cập nhật trạng thái bình thường (như PAID, SHIPPING)
        order.status = status_data.status
        db.commit()

    return {
        "message": f"Đã cập nhật đơn hàng {order_id} thành {status_data.status}", 
        "new_status": order.status
    }