from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import database, models
from pydantic import BaseModel

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

class StockUpdate(BaseModel):
    product_id: str
    quantity: int

@router.post("/import")
def import_stock(data: StockUpdate, db: Session = Depends(database.get_db)):
    # Cập nhật hoặc tạo mới tồn kho
    item = db.query(models.Inventory).filter(models.Inventory.product_id == data.product_id).first()
    if item:
        item.actual_stock += data.quantity
    else:
        item = models.Inventory(product_id=data.product_id, actual_stock=data.quantity)
        db.add(item)
    
    # Ghi log
    log = models.InventoryLog(product_id=data.product_id, change_amount=data.quantity, reason="Nhập hàng thủ công")
    db.add(log)
    db.commit()
    return {"message": f"Đã nhập thêm {data.quantity} sản phẩm {data.product_id}"}

@router.get("/status/{product_id}")
def check_stock(product_id: str, db: Session = Depends(database.get_db)):
    item = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not item:
        return {"product_id": product_id, "stock": 0}
    return {"product_id": product_id, "stock": item.actual_stock}