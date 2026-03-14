# File: KetibMall_App/src/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional

# ==========================================
# 1. DTO CHO SẢN PHẨM & ĐƠN HÀNG
# ==========================================
class ProductCreate(BaseModel):
    id: str
    name: str
    price: float
    cached_stock: int
    image_url: Optional[str] = None

class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]

# ==========================================
# 2. DTO CHO AUTH & USER
# ==========================================
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    # THÊM MỚI: Cho phép truyền role lúc tạo, mặc định là customer
    role: Optional[str] = "customer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# THÊM MỚI: Schema trả về User (Không chứa password để bảo mật)
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

# ==========================================
# 3. DTO CHO TOKEN (JWT)
# ==========================================
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse # Gửi kèm luôn thông tin User để Frontend hiển thị dễ dàng

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# ==========================================
# 4. DTO CHO CẬP NHẬT ĐƠN HÀNG
# ==========================================
class OrderStatusUpdate(BaseModel):
    status: str