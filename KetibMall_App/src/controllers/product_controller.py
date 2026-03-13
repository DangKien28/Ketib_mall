from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from src.models import database, models
import shutil
import os

# THÊM MỚI: Import trạm kiểm soát Admin
from src.dependencies import get_admin_user

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.post("/")
async def create_product(
    id: str = Form(...),
    name: str = Form(...),
    price: float = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    # THÊM MỚI: Đặt trạm kiểm soát tại đây. Chỉ Admin mới gọi được API này.
    admin_user: models.User = Depends(get_admin_user) 
):
    # 1. Kiểm tra trùng mã
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Mã sản phẩm đã tồn tại!")
    
    image_url = None
    # 2. Xử lý lưu file ảnh nếu có
    if image:
        file_location = f"static/uploads/{id}_{image.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"http://localhost:8000/{file_location}"

    # 3. Lưu vào Database
    new_product = models.Product(
        id=id, 
        name=name, 
        price=price, 
        image_url=image_url, 
        cached_stock=0
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {"message": "Thêm sản phẩm kèm ảnh thành công", "data": new_product}

# API Get giữ nguyên, vì ai cũng có quyền xem sản phẩm (không gắn trạm kiểm soát)
@router.get("/")
def get_products(db: Session = Depends(database.get_db)):
    return db.query(models.Product).all()