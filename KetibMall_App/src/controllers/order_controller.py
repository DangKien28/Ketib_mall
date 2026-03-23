from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid
import os
import stripe
import redis
import logging
from src.models import database, models
from src import schemas
from src.dependencies import get_current_user, get_admin_user
from src.integration.publisher.publisher import send_order_event, send_order_cancel_event
from src.controllers.shipping_controller import create_ghn_order_internal

# Thiết lập ghi nhật ký (Log) để theo dõi trong Docker
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# --- CẤU HÌNH HỆ THỐNG ---
# Lấy giá trị từ file .env
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_KEY
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN_URL = os.getenv("DOMAIN_URL", "http://localhost:8080")

# Kiểm tra việc nạp biến môi trường ngay khi khởi động
if not STRIPE_KEY:
    logger.error("❌ LOI: Khong tim thay STRIPE_SECRET_KEY. Hay kiem tra file .env va Docker config.")
else:
    # Chỉ in ra 5 ký tự đầu để bảo mật nhưng vẫn xác nhận được là đã nạp
    logger.info(f"✅ Da nap Stripe Key: {STRIPE_KEY[:8]}...")

# Cấu hình Redis
# Thêm dòng lấy REDIS_PASS
REDIS_HOST = os.getenv("REDIS_HOST", "redis_cache")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASS = os.getenv("REDIS_PASS") # Lấy mật khẩu từ file .env

# Truyền thêm password vào redis.Redis
redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    password=REDIS_PASS,
    decode_responses=True
)

# Ngưỡng tối thiểu của Stripe (VNĐ)
MIN_PAYMENT_AMOUNT = 15000 

# ==========================================
# 1. API CHO KHÁCH HÀNG: ĐẶT HÀNG & THANH TOÁN
# ==========================================
@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user) 
):
    # Kiểm tra lại một lần nữa trước khi gọi Stripe
    if not stripe.api_key:
        logger.error("❌ Stripe API Key bi trong khi thuc hien giao dich.")
        raise HTTPException(status_code=500, detail="May chu chua duoc cau hinh thanh toan.")

    order_id = f"DH{str(uuid.uuid4().int)[:5]}"
    new_order = models.Order(
        id=order_id,
        user_id=current_user.id,
        status="PENDING",
        shipping_address=order.shipping_address, # THÊM MỚI
        district_id=order.district_id,           # THÊM MỚI
        ward_code=order.ward_code,               # THÊM MỚI
        shipping_fee=order.shipping_fee
    )
    db.add(new_order)

    items_for_mq = []
    line_items = []
    total_amount = 0

    try:
        for item in order.items:
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
            if not variant:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"Sản phẩm {item.variant_id} không tồn tại.")
            
            if variant.cached_stock < item.quantity:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"Sản phẩm {variant.id} hết hàng.")
            
            price = int(variant.price)
            total_amount += price * item.quantity

            variant.cached_stock -= item.quantity
            db.add(models.OrderItem(order_id=order_id, variant_id=item.variant_id, quantity=item.quantity))
            items_for_mq.append({"variant_id": item.variant_id, "quantity": item.quantity})
            
            line_items.append({
                'price_data': {
                    'currency': 'vnd',
                    'product_data': {'name': f"Mã SP: {variant.id}"},
                    'unit_amount': price,
                },
                'quantity': item.quantity,
            })

        if order.shipping_fee and order.shipping_fee > 0:
            total_amount += order.shipping_fee
            line_items.append({
                'price_data': {
                    'currency': 'vnd',
                    'product_data': {'name': "Phí vận chuyển (Giao Hàng Nhanh)"},
                    'unit_amount': order.shipping_fee,
                },
                'quantity': 1,
            })

            
        # Kiểm tra tổng tiền tối thiểu (Lỗi 0.42$ bạn gặp trước đó)
        if total_amount < MIN_PAYMENT_AMOUNT:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Đơn hàng cần tối thiểu {MIN_PAYMENT_AMOUNT:,}đ.")

        db.commit()
        
        # Gọi Stripe tạo phiên thanh toán
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            client_reference_id=order_id, 
            success_url=f"{DOMAIN_URL}/app.html",
            cancel_url=f"{DOMAIN_URL}/app.html",
        )

        send_order_event({"order_id": order_id, "items": items_for_mq})
        redis_client.delete("all_products_cache")
        
        return {"checkout_url": checkout_session.url, "order_id": order_id}

    except stripe.error.AuthenticationError:
        db.rollback()
        logger.error("🔥 Stripe Authentication Error: Key khong hop le hoac bi tu choi.")
        raise HTTPException(status_code=500, detail="Loi xac thuc voi cong thanh toan Stripe.")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ LOI HE THONG: {str(e)}")
        raise HTTPException(status_code=500, detail="Loi may chu khi xu ly don hang.")

# ==========================================
# 2. WEBHOOK: TU DONG CAP NHAT PAID
# ==========================================
@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(database.get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return {"status": "error", "message": "Signature khong hop le"}

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get("client_reference_id")
        
        # Truy vấn lấy đơn hàng, thông tin User và các Items
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if order and order.status == "PENDING":
            order.status = "PAID"
            
            # --- BẮT ĐẦU ĐOẠN CODE THÊM MỚI ---
            user_info = db.query(models.User).filter(models.User.id == order.user_id).first()
            
            # Gọi hàm tạo đơn trên GHN
            ghn_response = create_ghn_order_internal(order, user_info, order.items)
            
            # Kiểm tra nếu tạo thành công thì lưu mã vận đơn lại
            if ghn_response and ghn_response.get("code") == 200:
                order.ghn_order_code = ghn_response["data"]["order_code"]
                logger.info(f"✅ Đã tạo đơn GHN thành công. Mã vận đơn: {order.ghn_order_code}")
            else:
                error_msg = ghn_response.get('message') if ghn_response else "Unknown error"
                logger.error(f"❌ Lỗi tạo đơn GHN cho Order {order_id}: {error_msg}")
            # --- KẾT THÚC ĐOẠN CODE THÊM MỚI ---

            db.commit()
            logger.info(f"✅ Don hang {order_id} da chuyen sang PAID.")

    return {"status": "success"}



# ==========================================
# 3. ADMIN API (GIU NGUYEN LOGIC CU)
# ==========================================
@router.get("")
@router.get("/")
def get_all_orders(db: Session = Depends(database.get_db), admin_user: models.User = Depends(get_admin_user)):
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    return [{
        "id": o.id, 
        "user_id": o.user_id, 
        "status": o.status, 
        "items_count": len(o.items),
        "ghn_order_code": o.ghn_order_code
    } for o in orders]

@router.put("/{order_id}/status")
def update_order_status(order_id: str, status_data: schemas.OrderStatusUpdate, db: Session = Depends(database.get_db), admin_user: models.User = Depends(get_admin_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Khong tim thay don hang.")

    if status_data.status == "CANCELED" and order.status != "CANCELED":
        for item in order.items:
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
            if variant: variant.cached_stock += item.quantity
        send_order_cancel_event({"order_id": order_id, "items": [{"variant_id": i.variant_id, "quantity": i.quantity} for i in order.items]})

    order.status = status_data.status
    db.commit()
    redis_client.delete("all_products_cache")
    return {"message": "Thành công", "new_status": order.status}