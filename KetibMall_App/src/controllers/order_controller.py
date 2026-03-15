from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid
import os
import redis

from src.models import database, models
from src import schemas
from src.dependencies import get_current_user, get_admin_user
from src.integration.publisher.publisher import send_order_event, send_order_cancel_event

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# ==========================================
# CẤU HÌNH REDIS & SEPAY
# ==========================================
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_PASS = os.getenv("REDIS_PASS")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASS, decode_responses=True)

SEPAY_BANK_BIN = os.getenv("SEPAY_BANK_BIN", "")
SEPAY_ACCOUNT_NO = os.getenv("SEPAY_ACCOUNT_NO", "")

# ==========================================
# 1. KHÁCH HÀNG ĐẶT HÀNG & TẠO LINK SEPAY
# ==========================================
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user) 
):
    # Mã đơn hàng ngắn gọn để khách dễ gõ nội dung chuyển khoản (VD: DH12345)
    order_id = f"DH{str(uuid.uuid4().int)[:5]}"
    new_order = models.Order(id=order_id, user_id=current_user.id, status="PENDING")
    db.add(new_order)

    items_for_mq = []
    total_amount = 0

    for item in order.items:
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
        if not variant or variant.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Sản phẩm {item.variant_id} không hợp lệ/hết hàng.")
        
        variant.cached_stock -= item.quantity
        order_item = models.OrderItem(order_id=order_id, variant_id=item.variant_id, quantity=item.quantity)
        db.add(order_item)
        items_for_mq.append({"variant_id": item.variant_id, "quantity": item.quantity})
        
        total_amount += int(variant.price) * item.quantity

    try:
        db.commit()
        send_order_event({"order_id": order_id, "items": items_for_mq})
        redis_client.delete("all_products_cache")
        
        # TẠO LINK TRANG THANH TOÁN QUÉT MÃ QR CỦA SEPAY
        # Cú pháp: pay.sepay.vn/s/[Bank_BIN]/[Account_No]?amount=...&note=...
        # checkout_url = f"https://pay.sepay.vn/s/{SEPAY_BANK_BIN}/{SEPAY_ACCOUNT_NO}?amount={total_amount}&note={order_id}"
        checkout_url = f"https://qr.sepay.vn/img?acc={SEPAY_ACCOUNT_NO}&bank=BIDV&amount={total_amount}&des={order_id}"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Đang chuyển hướng thanh toán...", "order_id": order_id, "checkout_url": checkout_url}

# ==========================================
# 2. WEBHOOK: SEPAY BÁO CÁO CÓ TIỀN VÀO TÀI KHOẢN
# ==========================================
@router.post("/sepay-webhook")
async def sepay_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Khi có người chuyển khoản thành công, máy chủ SePay sẽ bắn thông tin vào API này.
    Chúng ta sẽ đọc 'nội dung chuyển khoản' để tìm mã đơn hàng và cập nhật thành PAID.
    """
    data = await request.json()
    
    # Lấy nội dung chuyển khoản (Ví dụ: "NGUYEN VAN A CHUYEN TIEN DH12345")
    transfer_content = data.get("content", "").upper()
    transfer_amount = data.get("transferAmount", 0)
    
    # Tìm đơn hàng có mã trùng với nội dung chuyển khoản
    orders = db.query(models.Order).filter(models.Order.status == "PENDING").all()
    
    for order in orders:
        if order.id in transfer_content:
            # Nếu mã đơn xuất hiện trong lời nhắn chuyển khoản -> Đánh dấu Đã thanh toán
            order.status = "PAID"
            db.commit()
            print(f"🎉 [WEBHOOK] Đơn hàng {order.id} đã được thanh toán thành công ({transfer_amount} VNĐ)!")
            return {"success": True, "message": f"Updated order {order.id} to PAID"}
            
    return {"success": False, "message": "Không tìm thấy mã đơn hàng phù hợp."}

# ==========================================
# CÁC API CŨ (GET ORDERS & UPDATE STATUS)
# ==========================================
@router.get("/")
def get_all_orders(db: Session = Depends(database.get_db), admin_user: models.User = Depends(get_admin_user)):
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    return [{"id": o.id, "user_id": o.user_id, "status": o.status, "items_count": len(o.items)} for o in orders]

@router.put("/{order_id}/status")
def update_order_status(order_id: str, status_data: schemas.OrderStatusUpdate, db: Session = Depends(database.get_db), admin_user: models.User = Depends(get_admin_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order: raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
    
    valid_statuses = ["PENDING", "PAID", "SHIPPING", "COMPLETED", "CANCELED"]
    if status_data.status not in valid_statuses: raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")

    if status_data.status == "CANCELED" and order.status != "CANCELED":
        items_for_mq = []
        for item in order.items:
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
            if variant: variant.cached_stock += item.quantity
            items_for_mq.append({"variant_id": item.variant_id, "quantity": item.quantity})
        try:
            order.status = status_data.status
            db.commit()
            send_order_cancel_event({"order_id": order_id, "items": items_for_mq})
            redis_client.delete("all_products_cache")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi hủy đơn.")
    else:
        order.status = status_data.status
        db.commit()

    return {"message": f"Đã cập nhật đơn hàng {order_id} thành {status_data.status}", "new_status": order.status}