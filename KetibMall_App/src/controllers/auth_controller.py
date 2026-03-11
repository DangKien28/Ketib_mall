from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.models import database, models
from src import schemas
from passlib.context import CryptContext

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Cấu hình mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register")
async def register(user_data: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # 1. Kiểm tra email đã tồn tại chưa
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được đăng ký sử dụng."
        )

    # 2. Mã hóa mật khẩu
    hashed_pwd = get_password_hash(user_data.password)

    # 3. Tạo User mới
    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        username=user_data.email,
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
async def login(login_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    # 1. Tìm user theo email
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    
    # 2. Kiểm tra mật khẩu
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )

    return {
        "message": "Đăng nhập thành công!",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        }
    }