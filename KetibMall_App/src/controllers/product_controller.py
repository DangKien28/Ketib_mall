from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from sqlalchemy.orm import Session
from src.models import database, models
import os
import json
import redis
import logging
import cloudinary
import cloudinary.uploader
from fastapi.encoders import jsonable_encoder

# Import trạm kiểm soát Admin
from src.dependencies import get_admin_user

# ==========================================
# CẤU HÌNH REDIS
# ==========================================
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
REDIS_PASS = os.getenv("REDIS_PASS")

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASS, decode_responses=True
)
CACHE_KEY = "all_products_cache"

# Tạo công cụ ghi log
logger = logging.getLogger("KetibMall")
logger.setLevel(logging.INFO)

# ==========================================
# CẤU HÌNH CLOUDINARY (ĐÁM MÂY LƯU ẢNH)
# ==========================================

cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

router = APIRouter(prefix="/api/products", tags=["Products"])

# ==========================================
# 1. API ADMIN THÊM SẢN PHẨM & BIẾN THỂ (UPDATE CLOUDINARY)
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
    
    # ------ BẮN ẢNH LÊN ĐÁM MÂY CLOUDINARY ------
    image_url = None
    if image:
        try:
            logger.info(f"☁️ Đang tải ảnh {image.filename} lên Cloudinary...")
            # Upload file thẳng lên Cloudinary
            upload_result = cloudinary.uploader.upload(image.file)
            # Lấy đường link an toàn (https) do Cloudinary trả về
            image_url = upload_result.get("secure_url") 
            logger.info(f"✅ Đã tải ảnh lên mây thành công: {image_url}")
        except Exception as e:
            logger.error(f"❌ Lỗi tải ảnh lên Cloud: {str(e)}")
            raise HTTPException(status_code=500, detail="Lỗi khi tải ảnh lên Đám mây.")
    # --------------------------------------------

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
        redis_client.delete(CACHE_KEY)
        logger.info("🧹 [CACHE CLEARED] Đã dọn sạch tủ lạnh vì có sản phẩm mới!")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu Database: {str(e)}")

    return {"message": "Thêm sản phẩm thành công!", "product_id": new_product.id, "image_url": image_url}

# ==========================================
# 2. API LẤY DANH SÁCH SẢN PHẨM (KÈM BIẾN THỂ)
# ==========================================
@router.get("/")
def get_products(response: Response, db: Session = Depends(database.get_db)):
    cached_data = redis_client.get(CACHE_KEY)
    if cached_data:
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached_data)

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
        
    redis_client.setex(CACHE_KEY, 300, json.dumps(result))
    response.headers["X-Cache"] = "MISS"
    
    return result