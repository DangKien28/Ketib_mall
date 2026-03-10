# File: KetibMall_App/src/schemas.py

from pydantic import BaseModel
from typing import List, Optional

# DTO cho Sản phẩm
class ProductCreate(BaseModel):
    id: str
    name: str
    price: float
    cached_stock: int
    image_url: Optional[str] = None

# DTO cho Đơn hàng
class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]