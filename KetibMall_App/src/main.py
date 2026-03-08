# File: KetibMall_App/src/main.py

from typing import List
import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from src.models import database, models
from pydantic import BaseModel

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="KetibMall App API")
models.Base.metadata.create_all(bind=database.engine)

# Cấu hình CORS để cho phép file HTML gọi API mà không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hàm hỗ trợ kết nối Database
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Cấu trúc dữ liệu JSON khi thêm sản phẩm
class ProductCreate(BaseModel):
    id: str
    name: str
    price: float
    cached_stock: int

# Cấu trúc của 1 món hàng trong giỏ
class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int

# Cấu trúc của toàn bộ Đơn hàng gửi lên
class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]

@app.get("/")
def read_root():
    return {"message": "Server KetibMall_App đang hoạt động!"}

# API Lấy danh sách sản phẩm
@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

# API Thêm sản phẩm (Dùng để tạo dữ liệu mẫu)
@app.post("/api/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product.id).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Mã sản phẩm đã tồn tại!")
    
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Thêm thành công", "data": new_product}


# API 3: Đặt hàng (Nơi phép màu xảy ra)
@app.post("/api/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # 1. (Tự động hóa) Vì ta chưa có API Đăng ký, nên tự tạo 1 User mẫu nếu chưa có để không bị lỗi Khóa ngoại
    db_user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not db_user:
        new_user = models.User(id=order.user_id, username="Khach Hang Test", email="test@ketib.com")
        db.add(new_user)
        db.commit()

    # 2. Tạo mã đơn hàng ngẫu nhiên (VD: ORD-A1B2C)
    order_id = f"ORD-{str(uuid.uuid4())[:5].upper()}"

    # 3. Tạo Đơn hàng mới trạng thái PENDING
    new_order = models.Order(id=order_id, user_id=order.user_id, status="PENDING")
    db.add(new_order)

    # 4. Xử lý từng món hàng khách mua
    for item in order.items:
        # Kiểm tra sản phẩm có tồn tại không
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            db.rollback() # Hủy bỏ toàn bộ giao dịch nếu lỗi
            raise HTTPException(status_code=404, detail=f"Sản phẩm {item.product_id} không tồn tại!")

        # Kiểm tra số lượng tồn kho tạm
        if product.cached_stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Sản phẩm {product.name} chỉ còn {product.cached_stock} cái!")

        # Trừ tồn kho tạm ngay lập tức
        product.cached_stock -= item.quantity

        # Lưu chi tiết vào bảng order_items
        order_item = models.OrderItem(order_id=order_id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)

    # 5. Chốt (Commit) toàn bộ thay đổi vào Database
    db.commit()

    # =========================================================
    # TODO: [GIAI ĐOẠN 4] CHÚNG TA SẼ BẮN TIN NHẮN RABBITMQ Ở ĐÂY
    # =========================================================

    return {
        "message": "Đặt hàng thành công!", 
        "order_id": order_id,
        "status": "PENDING - Đang chờ Kho xác nhận"
    }