import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Chỉ định nơi Frontend có thể lấy Token (gọi sang cổng 8000 của App)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8000/api/auth/login")

def get_admin_user(token: str = Depends(oauth2_scheme)):
    """
    Trạm kiểm soát này chỉ làm 2 việc: 
    1. Dùng SECRET_KEY giải mã Token.
    2. Đọc xem "role" bên trong có phải "admin" không.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin. Vui lòng đăng nhập lại.",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: str = payload.get("role")
        
        # Kiểm tra quyền Admin
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Truy cập bị từ chối. Chỉ Quản trị viên mới được thao tác với Kho."
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn.")
    except jwt.PyJWTError:
        raise credentials_exception
        
    return payload # Trả về thông tin đã giải mã nếu qua trạm thành công