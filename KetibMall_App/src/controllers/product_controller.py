# File: KetibMall_App/src/controllers/product_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import database, models
from src.schemas import ProductCreate

router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)

@router.get("/")
def get_products(db: Session = Depends(database.get_db)):
    return db.query(models.Product).all()

@router.post("/")
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product.id).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Mã sản phẩm đã tồn tại!")
    
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Thêm sản phẩm thành công", "data": new_product}