# File: KetibMall_App_Inventory/src/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Dùng khi nhập hàng (Stock In)
class StockUpdate(BaseModel):
    product_id: str
    quantity: int

# Dùng khi hiển thị thông tin tồn kho
class InventoryBase(BaseModel):
    product_id: str
    actual_stock: int
    last_updated: datetime

    class Config:
        from_attributes = True

# Dùng khi xem lịch sử Log
class InventoryLogBase(BaseModel):
    id: int
    product_id: str
    change_amount: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True