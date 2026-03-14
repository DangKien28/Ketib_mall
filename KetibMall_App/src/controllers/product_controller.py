from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from src.models import database, models
import shutil
import os
import json

# Import trạm kiểm soát Admin
from src.dependencies import get_admin_user

router = APIRouter(prefix="/api/products", tags=["Products"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 1. API ADMIN THÊM SẢN PHẨM & BIẾN THỂ
# ==========================================
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: str = Form(...), # Nhận JSON thay vì từng trường
    image: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_admin_user) 
):
    try:
        data = json.loads(product_data)
    except:
        raise HTTPException(status_code=400, detail="Dữ liệu product_data phải là JSON hợp lệ.")
    
    # 1. Kiểm tra trùng mã
    db_product = db.query(models.Product).filter(models.Product.id == data.get('id')).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Mã sản phẩm đã tồn tại!")
    
    image_url = None
    # 2. Xử lý lưu file ảnh nếu có
    if image:
        file_location = os.path.join(UPLOAD_DIR, f"{data.get('id')}_{image.filename}")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"http://localhost:8000/{file_location}"

    # 3. Lưu Sản Phẩm Gốc
    new_product = models.Product(
        id=data.get('id'), 
        name=data.get('name'), 
        image_url=image_url
    )
    db.add(new_product)

    # 4. Lưu Các Biến Thể (Variants)
    variants_list = data.get('variants', [])
    if not variants_list:
        db.rollback()
        raise HTTPException(status_code=400, detail="Sản phẩm phải có ít nhất 1 biến thể (Size/Màu).")
        
    for v in variants_list:
        # Tạo ID biến thể: Ví dụ "SP01-M-RED"
        variant_id = f"{data.get('id')}-{v.get('size')}-{v.get('color')}".upper()
        
        new_variant = models.ProductVariant(
            id=variant_id,
            product_id=data.get('id'),
            size=v.get('size'),
            color=v.get('color'),
            price=v.get('price'),
            cached_stock=0
        )
        db.add(new_variant)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu Database: {str(e)}")

    return {"message": "Thêm sản phẩm và biến thể thành công!", "product_id": new_product.id}

# ==========================================
# 2. API LẤY DANH SÁCH SẢN PHẨM (KÈM BIẾN THỂ)
# ==========================================
@router.get("/")
def get_products(db: Session = Depends(database.get_db)):
    products = db.query(models.Product).all()
    
    result = []
    for p in products:
        variants = []
        for v in p.variants:
            variants.append({
                "variant_id": v.id,
                "size": v.size,
                "color": v.color,
                "price": v.price,
                "cached_stock": v.cached_stock
            })
            
        result.append({
            "id": p.id,
            "name": p.name,
            "image_url": p.image_url,
            "variants": variants # Lồng danh sách biến thể vào sản phẩm
        })
        
    return result