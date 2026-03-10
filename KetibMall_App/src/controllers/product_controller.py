from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form # <--- THÊM IMPORT
from sqlalchemy.orm import Session
from src.models import database, models
import shutil
import os

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.post("/")
async def create_product(
    id: str = Form(...),            # Nhận dữ liệu từ Form thay vì JSON
    name: str = Form(...),
    price: float = Form(...),
    image: UploadFile = File(None), # Nhận file ảnh (không bắt buộc)
    db: Session = Depends(database.get_db)
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
        # Tạo URL đầy đủ để Frontend truy cập
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

# API Get giữ nguyên
@router.get("/")
def get_products(db: Session = Depends(database.get_db)):
    return db.query(models.Product).all()