import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # 1. Tạo một bản sao của dữ liệu để không làm ảnh hưởng dữ liệu gốc
    to_encode = data.copy()
    
    # 2. Thiết lập thời gian hết hạn cho Token
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 3. Gắn thêm thông tin thời gian hết hạn (exp) vào dữ liệu chuẩn bị mã hóa
    to_encode.update({"exp": expire})
    
    # 4. Dùng thư viện jwt để tạo chuỗi Token
    # Đầu vào gồm: Dữ liệu (Payload), Chữ ký bí mật (Secret Key), Thuật toán (Algorithm)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt