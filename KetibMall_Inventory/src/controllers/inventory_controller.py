from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import database, models
from src import schemas # Import file schemas vừa sửa ở trên
from src.integration.publisher.publisher import send_stock_update 

# Import Trạm kiểm soát Admin
from src.dependencies import get_admin_user

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.post("/import")
def import_stock(
    data: schemas.StockUpdate, # Dùng Schema StockUpdate mới
    db: Session = Depends(database.get_db),
    admin_info: dict = Depends(get_admin_user) # Trạm kiểm tra Token
):
    # 1. Cập nhật hoặc tạo mới tồn kho theo BIẾN THỂ (variant_id)
    item = db.query(models.Inventory).filter(models.Inventory.variant_id == data.variant_id).first()
    if item:
        item.actual_stock += data.quantity
    else:
        item = models.Inventory(variant_id=data.variant_id, actual_stock=data.quantity)
        db.add(item)
    
    # 2. Ghi log lịch sử nhập hàng
    admin_email = admin_info.get("sub", "Unknown Admin") if isinstance(admin_info, dict) else getattr(admin_info, "email", "Admin")
    log = models.InventoryLog(
        variant_id=data.variant_id, 
        change_amount=data.quantity, 
        reason=f"Nhập hàng thủ công qua API bởi: {admin_email}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(item)
    
    # 3. PHÁT TIN NHẮN ĐỒNG BỘ:
    try:
        send_stock_update(item.variant_id, item.actual_stock)
        sync_status = "Đã gửi tín hiệu đồng bộ sang App"
    except Exception as e:
        sync_status = f"Lỗi gửi tín hiệu đồng bộ: {str(e)}"
    
    return {
        "message": f"Đã nhập thêm {data.quantity} sản phẩm cho mã {data.variant_id}",
        "current_actual_stock": item.actual_stock,
        "sync_status": sync_status
    }

@router.get("/status/{variant_id}")
def check_stock(variant_id: str, db: Session = Depends(database.get_db)):
    item = db.query(models.Inventory).filter(models.Inventory.variant_id == variant_id).first()
    if not item:
        return {"variant_id": variant_id, "stock": 0, "message": "Biến thể không tồn tại trong kho"}
    return {
        "variant_id": variant_id, 
        "stock": item.actual_stock,
        "last_updated": item.last_updated
    }