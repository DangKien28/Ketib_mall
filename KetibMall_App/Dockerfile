# Sử dụng Python phiên bản nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các công cụ hệ thống cần thiết cho psycopg2 (nếu dùng postgres)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Sao chép file yêu cầu thư viện vào trước để tận dụng cache của Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mở cổng 8000 cho FastAPI
EXPOSE 8000

# Lệnh mặc định (Sẽ bị ghi đè bởi docker-compose nếu là Worker)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]