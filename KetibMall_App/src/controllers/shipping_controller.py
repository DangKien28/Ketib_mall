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
    

def create_ghn_order_internal(order, user_info, items):
    api_url = os.getenv("GHN_API_URL", "https://dev-online-gateway.ghn.vn/shiip/public-api/v2")
    token = os.getenv("GHN_API_TOKEN")
    shop_id = os.getenv("GHN_SHOP_ID")
    from_district = int(os.getenv("GHN_FROM_DISTRICT_ID", 1442))

    url = f"{api_url}/shipping-order/create"
    headers = {
        "token": token,
        "ShopId": shop_id
    }

    # Format danh sách sản phẩm theo chuẩn của GHN
    ghn_items = []
    for item in items:
        ghn_items.append({
            "name": f"Sản phẩm mã {item.variant_id}",
            "quantity": item.quantity,
            "weight": 200 # Ước lượng hoặc lấy từ database
        })

    payload = {
        "payment_type_id": 1, # 1: Shop trả phí ship (Vì khách đã trả kèm vào bill Stripe rồi)
        "note": f"Đơn hàng {order.id} từ Ketib Mall",
        "required_note": "CHOXEMHANGKHONGTHU", # Quy định xem hàng
        "to_name": user_info.full_name or "Khách hàng", # Lấy từ user
        #"to_phone": user_info.phone or "0999999999",    # Lấy từ user
        "to_phone": "0999999999", 
        "to_address": order.shipping_address,
        "to_ward_code": str(order.ward_code),
        "to_district_id": order.district_id,
        "cod_amount": 0, # QUAN TRỌNG: Khách đã thanh toán qua Stripe nên COD phải = 0
        "content": "Quần áo / Sản phẩm Ketib Mall",
        "weight": len(items) * 200, # Tổng trọng lượng (gram)
        "length": 15,
        "width": 15,
        "height": 10,
        "service_type_id": 2, # Chuyển phát TMĐT
        "items": ghn_items
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Lỗi khi gọi API GHN Create Order: {e}")
        return None