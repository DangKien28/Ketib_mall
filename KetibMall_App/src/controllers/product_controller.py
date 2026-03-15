from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from sqlalchemy.orm import Session
from src.models import database, models
import shutil
import os
import json
import redis
from fastapi.encoders import jsonable_encoder
import logging

# Import trạm kiểm soát Admin
from src.dependencies import get_admin_user

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_PASS = os.getenv("REDIS_PASS")

# Kết nối Redis an toàn có kèm Password
redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    db=REDIS_DB, 
    password=REDIS_PASS,
    decode_responses=True
)

CACHE_KEY = "all_products_cache"

# Tạo công cụ ghi log
logger = logging.getLogger("KetibMall")
logger.setLevel(logging.INFO)


router = APIRouter(prefix="/api/products", tags=["Products"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 1. API ADMIN THÊM SẢN PHẨM & BIẾN THỂ
# ==========================================
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_admin_user) 
):
    try:
        data = json.loads(product_data)
    except:
        raise HTTPException(status_code=400, detail="Dữ liệu product_data phải là JSON hợp lệ.")
    
    db_product = db.query(models.Product).filter(models.Product.id == data.get('id')).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Mã sản phẩm đã tồn tại!")
    
    image_url = None
    if image:
        file_location = os.path.join(UPLOAD_DIR, f"{data.get('id')}_{image.filename}")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/{file_location}"

    new_product = models.Product(id=data.get('id'), name=data.get('name'), image_url=image_url)
    db.add(new_product)

    variants_list = data.get('variants', [])
    if not variants_list:
        db.rollback()
        raise HTTPException(status_code=400, detail="Phải có ít nhất 1 biến thể.")
        
    for v in variants_list:
        variant_id = f"{data.get('id')}-{v.get('size')}-{v.get('color')}".upper()
        new_variant = models.ProductVariant(
            id=variant_id, product_id=data.get('id'), size=v.get('size'),
            color=v.get('color'), price=v.get('price'), cached_stock=0
        )
        db.add(new_variant)

    try:
        db.commit()
        # ------ PHÉP THUẬT REDIS Ở ĐÂY ------
        redis_client.delete(CACHE_KEY)
        logger.info("🧹 [CACHE CLEARED] Đã dọn sạch tủ lạnh vì có sản phẩm mới!")
        # ------------------------------------
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu Database: {str(e)}")

    return {"message": "Thêm sản phẩm thành công!", "product_id": new_product.id}

# ==========================================
# 2. API LẤY DANH SÁCH SẢN PHẨM (KÈM BIẾN THỂ)
# ==========================================
@router.get("/")
def get_products(response: Response, db: Session = Depends(database.get_db)):
    # ------ PHÉP THUẬT REDIS (LẤY RA) ------
    cached_data = redis_client.get(CACHE_KEY)
    if cached_data:
        logger.info("⚡ [CACHE HIT] Lấy sản phẩm từ Tủ lạnh Redis")
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached_data)
    # ----------------------------------------

    logger.info("🐌 [CACHE MISS] Lấy sản phẩm từ Database")
    products = db.query(models.Product).all()
    
    result = []
    for p in products:
        variants = []
        for v in p.variants:
            variants.append({
                "variant_id": v.id, "size": v.size, "color": v.color,
                "price": v.price, "cached_stock": v.cached_stock
            })
            
        result.append({
            "id": p.id, "name": p.name, "image_url": p.image_url, "variants": variants
        })
        
    # ------ PHÉP THUẬT REDIS (CẤT VÀO) ------
    redis_client.setex(CACHE_KEY, 300, json.dumps(result))
    response.headers["X-Cache"] = "MISS"
    # ----------------------------------------
    
    return result