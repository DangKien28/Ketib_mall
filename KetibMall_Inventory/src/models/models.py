from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

# Bảng tồn kho thực tế
class Inventory(Base):
    __tablename__ = "inventory"
    product_id = Column(String, primary_key=True)
    actual_stock = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

# Bảng lịch sử nhập/xuất kho
class InventoryLog(Base):
    __tablename__ = "inventory_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String)
    change_amount = Column(Integer) # Số dương là nhập, số âm là xuất
    reason = Column(String) # Ví dụ: "Import", "Order ORD-123"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)