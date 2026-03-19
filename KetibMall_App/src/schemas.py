# File: KetibMall_App/src/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional

# ==========================================
# 1. DTO CHO SẢN PHẨM & BIẾN THỂ (CẬP NHẬT)
# ==========================================
class ProductVariantCreate(BaseModel):
    size: str
    color: str
    price: float

class ProductCreate(BaseModel):
    id: str
    name: str
    variants: List[ProductVariantCreate] # Nhận danh sách biến thể

class OrderItemCreate(BaseModel):
    variant_id: str # Đổi từ product_id thành variant_id
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]
    shipping_address: Optional[str] = None
    district_id: Optional[int] = None
    ward_code: Optional[str] = None
    shipping_fee: Optional[int] = 0
# ==========================================
# 2. DTO CHO AUTH & USER (GIỮ NGUYÊN)
# ==========================================
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = "customer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

# ==========================================
# 3. DTO CHO TOKEN (JWT) (GIỮ NGUYÊN)
# ==========================================
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# ==========================================
# 4. DTO CHO CẬP NHẬT ĐƠN HÀNG (GIỮ NGUYÊN)
# ==========================================
class OrderStatusUpdate(BaseModel):
    status: str