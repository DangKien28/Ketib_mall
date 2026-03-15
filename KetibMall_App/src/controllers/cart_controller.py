from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
import redis
from src.dependencies import get_current_user
from src.models import models

# Khai báo Router cho Giỏ hàng
router = APIRouter(prefix="/api/cart", tags=["Cart"])

# --- KẾT NỐI REDIS ---
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_PASS = os.getenv("REDIS_PASS")

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASS, decode_responses=True
)
# ---------------------

# Khung dữ liệu khi khách gửi yêu cầu Thêm vào giỏ
class CartItem(BaseModel):
    variant_id: str
    quantity: int

# 1. API Lấy toàn bộ Giỏ hàng của User hiện tại
@router.get("/")
def get_cart(current_user: models.User = Depends(get_current_user)):
    # Tìm cái làn có dán mã số của User này
    cart_key = f"cart:{current_user.id}"
    
    # Lấy toàn bộ đồ trong làn ra (Kết quả dạng Dictionary: {"SP01-M-RED": "2"})
    cart_data = redis_client.hgetall(cart_key)
    
    return {"user_id": current_user.id, "cart": cart_data}

# 2. API Thêm/Sửa số lượng sản phẩm trong Giỏ
@router.post("/add")
def add_to_cart(item: CartItem, current_user: models.User = Depends(get_current_user)):
    cart_key = f"cart:{current_user.id}"
    
    # Kiểm tra xem món này đã có trong giỏ chưa
    current_qty = redis_client.hget(cart_key, item.variant_id)
    
    # Nếu có rồi thì cộng dồn, chưa có thì lấy số lượng mới
    if current_qty:
        new_qty = int(current_qty) + item.quantity
    else:
        new_qty = item.quantity
        
    # Nếu số lượng tụt xuống 0 hoặc âm thì xóa luôn món đó khỏi giỏ
    if new_qty <= 0:
        redis_client.hdel(cart_key, item.variant_id)
        new_qty = 0
    else:
        # Cất đồ vào giỏ
        redis_client.hset(cart_key, item.variant_id, new_qty)
        
    # Gia hạn thời gian tồn tại của Giỏ hàng (VD: 7 ngày = 604800 giây)
    # Nếu 7 ngày khách không mua, Tủ lạnh tự vứt giỏ hàng đi cho nhẹ máy
    redis_client.expire(cart_key, 604800)
    
    return {
        "message": "Đã cập nhật giỏ hàng!", 
        "variant_id": item.variant_id, 
        "quantity": new_qty
    }

# 3. API Xóa hẳn 1 món khỏi Giỏ
@router.delete("/remove/{variant_id}")
def remove_from_cart(variant_id: str, current_user: models.User = Depends(get_current_user)):
    cart_key = f"cart:{current_user.id}"
    redis_client.hdel(cart_key, variant_id)
    return {"message": f"Đã xóa {variant_id} khỏi giỏ hàng!"}