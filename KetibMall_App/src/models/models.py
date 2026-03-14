from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="customer")
    orders = relationship("Order", back_populates="owner")

# --- BẢNG SẢN PHẨM GỐC ---
class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True) # VD: "SP01"
    name = Column(String, index=True)
    image_url = Column(String, nullable=True)
    
    # Quan hệ 1-Nhiều với Biến thể
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

# --- BẢNG BIẾN THỂ (SIZE/MÀU) ---
class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(String, primary_key=True, index=True) # VD: "SP01-M-RED"
    product_id = Column(String, ForeignKey("products.id"))
    size = Column(String)
    color = Column(String)
    price = Column(Float)
    cached_stock = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="variants")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="PENDING")
    owner = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"))
    # LƯU Ý: Giờ đây khách hàng mua "Biến thể" chứ không mua "Sản phẩm gốc" nữa
    variant_id = Column(String, ForeignKey("product_variants.id")) 
    quantity = Column(Integer)
    
    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")