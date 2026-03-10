from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.models import database, models
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Cấu hình mã hóa mật khẩu bằng thuật toán Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schema dữ liệu cho Đăng ký
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

# Schema dữ liệu cho Đăng nhập
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- CÁC HÀM TIỆN ÍCH ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- CÁC ENDPOINT API ---

@router.post("/register")
async def register(user_data: RegisterRequest, db: Session = Depends(database.get_db)):
    # 1. Kiểm tra xem email đã tồn tại trong DB chưa
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được đăng ký sử dụng."
        )

    # 2. Mã hóa mật khẩu
    hashed_pwd = get_password_hash(user_data.password)

    # 3. Tạo User mới và lưu vào database
    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        username=user_data.email,  # Mặc định lấy email làm username
        password=hashed_pwd
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "Đăng ký tài khoản thành công!", "user_id": new_user.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo tài khoản.")

@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(database.get_db)):
    # 1. Tìm user theo email
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    
    # 2. Kiểm tra sự tồn tại và xác thực mật khẩu
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )

    # 3. Trả về thông tin cơ bản (Trong thực tế bạn sẽ trả về JWT Token ở đây)
    return {
        "message": "Đăng nhập thành công!",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        }
    }