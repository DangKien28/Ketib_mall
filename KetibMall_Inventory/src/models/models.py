from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base, engine 

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    # Mã sản phẩm khớp với bảng products bên App (VD: 'SP01')
    product_id = Column(String(20), primary_key=True, index=True) 
    actual_stock = Column(Integer, nullable=False, default=0)
    warehouse_location = Column(String(50), nullable=True) # Vị trí kệ hàng

class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(20), ForeignKey("inventory_items.product_id"))
    change_amount = Column(Integer, nullable=False) # VD: +50 (nhập), -2 (xuất)
    action_type = Column(String(50), nullable=False) # VD: 'RESTOCK', 'ORDER_RESERVE'
    reference_order_id = Column(String(20), nullable=True) # Lưu lại mã đơn hàng để đối soát

if __name__ == "__main__":
    print("Đang kết nối đến ketib_inventory_db (Port 5433) và tạo bảng...")
    Base.metadata.create_all(bind=engine)
    print("Thành công! Hãy mở Database Client kiểm tra DB Kho.")