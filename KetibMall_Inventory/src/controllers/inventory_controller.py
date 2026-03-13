from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import database, models
from pydantic import BaseModel
from src.integration.publisher.publisher import send_stock_update 

# THÊM MỚI: Import Trạm kiểm soát Admin
from src.dependencies import get_admin_user

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

class StockUpdate(BaseModel):
    product_id: str
    quantity: int

# THÊM MỚI: Gắn dependency get_admin_user vào API Nhập kho
@router.post("/import")
def import_stock(
    data: StockUpdate, 
    db: Session = Depends(database.get_db),
    admin_info: dict = Depends(get_admin_user) # Trạm kiểm tra Token
):
    # 1. Cập nhật hoặc tạo mới tồn kho trong Database của Inventory
    item = db.query(models.Inventory).filter(models.Inventory.product_id == data.product_id).first()
    if item:
        item.actual_stock += data.quantity
    else:
        # Nếu sản phẩm chưa tồn tại trong kho, tạo mới
        item = models.Inventory(product_id=data.product_id, actual_stock=data.quantity)
        db.add(item)
    
    # 2. Ghi log lịch sử nhập hàng (Bạn có thể lấy email từ admin_info để ghi log người nhập)
    admin_email = admin_info.get("sub", "Unknown Admin")
    log = models.InventoryLog(
        product_id=data.product_id, 
        change_amount=data.quantity, 
        reason=f"Nhập hàng thủ công qua API bởi: {admin_email}"
    )
    db.add(log)
    
    # Lưu các thay đổi vào Database
    db.commit()
    db.refresh(item)
    
    # 3. PHÁT TIN NHẮN ĐỒNG BỘ: 
    # Gửi thông tin tổng tồn kho mới nhất sang cho App (Port 8000)
    try:
        send_stock_update(item.product_id, item.actual_stock)
        sync_status = "Đã gửi tín hiệu đồng bộ sang App"
    except Exception as e:
        sync_status = f"Lỗi gửi tín hiệu đồng bộ: {str(e)}"
    
    return {
        "message": f"Đã nhập thêm {data.quantity} sản phẩm {data.product_id}",
        "current_actual_stock": item.actual_stock,
        "sync_status": sync_status
    }

# API Get status giữ nguyên (ai cũng xem được tồn kho để hiển thị)
@router.get("/status/{product_id}")
def check_stock(product_id: str, db: Session = Depends(database.get_db)):
    item = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not item:
        return {"product_id": product_id, "stock": 0, "message": "Sản phẩm không tồn tại trong kho"}
    return {
        "product_id": product_id, 
        "stock": item.actual_stock,
        "last_updated": item.last_updated
    }