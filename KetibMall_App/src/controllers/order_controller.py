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
    # 1. Kiểm tra User có tồn tại thực sự trong Database hay không
    # Không còn tự động tạo user_id = 1 như phiên bản cũ
    db_user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=404, 
            detail="Người dùng không hợp lệ hoặc chưa đăng nhập. Vui lòng kiểm tra lại."
        )

    # 2. Khởi tạo ID đơn hàng duy nhất
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"
    # Gắn thông tin user_id thực tế lấy từ yêu cầu của Frontend
    new_order = models.Order(id=order_id, user_id=order.user_id, status="PENDING")
    db.add(new_order)

    # Dùng để chứa thông tin gửi sang RabbitMQ cho dịch vụ Inventory
    items_for_mq = []

    # 3. Duyệt danh sách sản phẩm trong đơn hàng
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        # Kiểm tra tồn kho tại chỗ (cached_stock) trong Database App
        if not product or product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(
                status_code=400, 
                detail=f"Sản phẩm {item.product_id} không đủ hàng hoặc không tồn tại!"
            )
        
        # Trừ kho tạm trên App Service để khách hàng thấy thay đổi ngay lập tức
        product.cached_stock -= item.quantity
        
        # Lưu chi tiết các mặt hàng vào đơn hàng
        order_item = models.OrderItem(
            order_id=order_id, 
            product_id=item.product_id, 
            quantity=item.quantity
        )
        db.add(order_item)
        
        # Thêm vào danh sách để gửi lệnh trừ kho thực tế sang dịch vụ Inventory
        items_for_mq.append({"product_id": item.product_id, "quantity": item.quantity})

    # 4. Xác nhận lưu thay đổi vào Database của App Service
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi lưu đơn hàng.")

    # 5. PHÁT TIN NHẮN SANG KHO (RabbitMQ) để xử lý kho thực tế
    order_payload = {
        "order_id": order_id,
        "items": items_for_mq
    }
    
    try:
        send_order_event(order_payload)
    except Exception as e:
        # Ghi log nếu gửi tin thất bại để xử lý sau (tồn kho thực tế sẽ được đồng bộ lại sau)
        print(f"Lỗi gửi tin nhắn đồng bộ kho: {e}")

    return {
        "message": "Đặt hàng thành công! Đã gửi thông tin sang hệ thống Kho để xử lý.",
        "order_id": order_id,
        "user": db_user.full_name
    }