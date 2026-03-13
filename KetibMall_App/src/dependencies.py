from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from src.models import database, models
from src import schemas
from src.security import SECRET_KEY, ALGORITHM

# Khai báo cơ chế bắt Token (FastAPI sẽ tự động lấy chuỗi Token từ Header của Request)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==========================================
# TRẠM KIỂM SOÁT 1: BẮT BUỘC ĐÃ ĐĂNG NHẬP
# ==========================================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Hàm này kiểm tra xem Token có hợp lệ và còn hạn hay không.
    Nếu hợp lệ, nó trả về thông tin của User đó.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã Token bằng Chìa khóa bí mật
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
        )
    except jwt.PyJWTError:
        raise credentials_exception

    # Đối chiếu với Database để chắc chắn User này vẫn còn tồn tại
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user

# ==========================================
# TRẠM KIỂM SOÁT 2: BẮT BUỘC LÀ ADMIN
# ==========================================
def get_admin_user(current_user: models.User = Depends(get_current_user)):
    """
    Hàm này chạy qua Trạm 1 trước. Nếu qua được, nó kiểm tra tiếp xem Role có phải là 'admin' không.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # Lỗi 403: Không đủ quyền hạn
            detail="Truy cập bị từ chối. Chỉ Quản trị viên (Admin) mới có quyền thực hiện thao tác này."
        )
    return current_user