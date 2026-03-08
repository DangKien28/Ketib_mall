# File: KetibMall_App/src/models/models.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base, engine  # Import từ file database.py vừa tạo

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(String(20), primary_key=True, index=True) # VD: 'SP01'
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    cached_stock = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String(20), primary_key=True, index=True) # VD: 'ORD-999'
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="PENDING")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(20), ForeignKey("orders.id"))
    product_id = Column(String(20), ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)

if __name__ == "__main__":
    print("Đang kết nối đến ketib_app_db và tạo bảng...")
    # Lệnh thần thánh: tự động sinh ra các bảng trong database
    Base.metadata.create_all(bind=engine)
    print("Thành công! Hãy mở Database Client để kiểm tra.")