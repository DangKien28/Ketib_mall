# Tạo mới file: KetibMall_App/src/controllers/shipping_controller.py
from fastapi import APIRouter, HTTPException
import os
import requests # Thư viện gọi API (có sẵn trong hầu hết dự án Python)

router = APIRouter(prefix="/api/shipping", tags=["Shipping"])

@router.post("/calculate")
def calculate_shipping_fee(district_id: int, ward_code: str, weight: int = 500):
    # Lấy biến môi trường đã cài ở Epic 1
    api_url = os.getenv("GHN_API_URL", "https://dev-online-gateway.ghn.vn/shiip/public-api/v2")
    token = os.getenv("GHN_API_TOKEN")
    shop_id = os.getenv("GHN_SHOP_ID")
    from_district = int(os.getenv("GHN_FROM_DISTRICT_ID", 1442))

    url = f"{api_url}/shipping-order/fee"
    headers = {
        "token": token,
        "ShopId": shop_id
    }
    payload = {
        "service_type_id": 2, # Mã 2 = Chuyển phát thương mại điện tử
        "from_district_id": from_district,
        "to_district_id": district_id,
        "to_ward_code": str(ward_code),
        "weight": weight,
        "insurance_value": 0 # Có thể lấy tổng giá trị đơn hàng đưa vào đây để tính phí bảo hiểm
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if data.get("code") == 200:
            return {"shipping_fee": data["data"]["total"]}
        else:
            print(f"Lỗi GHN: {data.get('message')}")
            # Fallback (Dự phòng): Nếu GHN báo lỗi, lấy phí ship mặc định 30k để khách vẫn mua được hàng
            return {"shipping_fee": 30000} 
            
    except Exception as e:
        print(f"Lỗi gọi API GHN: {e}")
        return {"shipping_fee": 30000} # Fallback khi rớt mạng