# File: KetibMall_Inventory/src/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Dùng khi nhập hàng (Stock In)
class StockUpdate(BaseModel):
    variant_id: str # Đổi từ product_id thành variant_id
    quantity: int

# Dùng khi hiển thị thông tin tồn kho
class InventoryBase(BaseModel):
    variant_id: str # Đổi từ product_id thành variant_id
    actual_stock: int
    last_updated: datetime

    class Config:
        from_attributes = True

# Dùng khi xem lịch sử Log
class InventoryLogBase(BaseModel):
    id: int
    variant_id: str # Đổi từ product_id thành variant_id
    change_amount: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True