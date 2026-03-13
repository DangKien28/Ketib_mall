let cart = [];

document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    updateCartUI(); // Gọi hàm render giỏ hàng ngay khi load
    
    // Hiển thị tên người dùng nếu đã đăng nhập
    const userStr = localStorage.getItem('user');
    const userInfoDiv = document.getElementById('user-info');
    if (userStr && userInfoDiv) {
        const user = JSON.parse(userStr);
        userInfoDiv.innerHTML = `Xin chào, <b class="text-blue-600" id="personal">${user.full_name || user.email}</b>`;
    }
});

function redirect_to_personal() {
    
}

async function loadProducts() {
    try {
        const response = await fetch('http://localhost:8000/api/products/');
        const products = await response.json();
        const grid = document.getElementById('product-grid');
        if (!grid) return;

        grid.innerHTML = '';
        products.forEach(p => {
            const imageTag = p.image_url 
                ? `<img src="${p.image_url}" alt="${p.name}" class="w-full h-48 object-cover rounded-md mb-4 shadow-sm">`
                : `<div class="w-full h-48 bg-gray-100 rounded-md mb-4 flex items-center justify-center text-gray-400">No Image</div>`;
            
            grid.innerHTML += `
                <div class="border p-4 rounded-lg shadow-sm hover:shadow-md transition bg-white flex flex-col">
                    ${imageTag}
                    <h3 class="font-bold text-lg text-gray-800">${p.name}</h3>
                    <p class="text-red-500 font-bold my-2">${p.price.toLocaleString()} VNĐ</p>
                    <p class="text-gray-500 text-sm mb-4">Kho tạm: <span class="font-mono font-bold ${p.cached_stock > 0 ? 'text-green-600' : 'text-red-500'}">${p.cached_stock}</span></p>
                    <button onclick="addToCart('${p.id}', '${p.name}', ${p.price})" 
                            class="mt-auto bg-blue-600 text-white font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                            ${p.cached_stock <= 0 ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                        ${p.cached_stock > 0 ? 'Thêm vào giỏ' : 'Hết hàng'}
                    </button>
                </div>
            `;
        });
    } catch (error) {
        console.error('Lỗi tải sản phẩm:', error);
    }
}

// ==========================================
// LOGIC GIỎ HÀNG (CART LOGIC)
// ==========================================
function addToCart(id, name, price) {
    const existing = cart.find(item => item.id === id || item.product_id === id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ id: id, product_id: id, name: name, price: price, quantity: 1 });
    }
    
    updateCartUI();

    // Mở Sidebar mượt mà
    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar) {
        sidebar.classList.remove('translate-x-full');
    }
}

function increaseQuantity(id) {
    const item = cart.find(i => i.id === id || i.product_id === id);
    if (item) {
        item.quantity += 1;
        updateCartUI();
    }
}

function decreaseQuantity(id) {
    const index = cart.findIndex(i => i.id === id || i.product_id === id);
    if (index !== -1) {
        if (cart[index].quantity > 1) {
            cart[index].quantity -= 1;
        } else {
            // Xóa khỏi giỏ nếu số lượng lùi về 0
            cart.splice(index, 1);
        }
        updateCartUI();
    }
}

function updateCartUI() {
    // 1. Cập nhật số lượng bong bóng đỏ trên icon Giỏ hàng
    const countSpan = document.getElementById('cart-count');
    if (countSpan) {
        countSpan.innerText = cart.reduce((sum, item) => sum + item.quantity, 0);
    }

    // 2. Vẽ lại danh sách sản phẩm trong Sidebar
    const list = document.getElementById('cart-items');
    if (!list) return;

    list.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        list.innerHTML = '<div class="text-center text-gray-500 mt-10">Giỏ hàng của bạn đang trống.</div>';
        document.getElementById('cart-total').innerText = '0 VNĐ';
        return;
    }

    cart.forEach(item => {
        total += item.price * item.quantity;
        const itemId = item.id || item.product_id;
        
        // Vẽ thẻ HTML có nút (+) (-)
        list.innerHTML += `
            <div class="flex justify-between items-center border-b border-gray-100 py-4">
                <div class="flex-1 pr-4">
                    <h4 class="font-semibold text-gray-800 text-sm leading-tight">${item.name}</h4>
                    <p class="text-red-500 font-bold text-sm mt-1">${item.price.toLocaleString()} đ</p>
                </div>
                <div class="flex items-center gap-3 bg-gray-50 px-2 py-1 rounded-lg border border-gray-200">
                    <button onclick="decreaseQuantity('${itemId}')" class="text-gray-500 hover:text-red-500 font-bold px-1 transition">-</button>
                    <span class="w-6 text-center text-sm font-semibold">${item.quantity}</span>
                    <button onclick="increaseQuantity('${itemId}')" class="text-gray-500 hover:text-green-600 font-bold px-1 transition">+</button>
                </div>
            </div>
        `;
    });

    // 3. Cập nhật tổng tiền
    const totalDiv = document.getElementById('cart-total');
    if (totalDiv) {
        totalDiv.innerText = `${total.toLocaleString()} VNĐ`;
    }
}

// Nút đóng Sidebar
const closeCartBtn = document.getElementById('close-cart');
if (closeCartBtn) {
    closeCartBtn.addEventListener('click', () => {
        const sidebar = document.getElementById('cart-sidebar');
        if (sidebar) sidebar.classList.add('translate-x-full');
    });
}

// Nút mở Sidebar thủ công
const cartBtn = document.getElementById('cart-btn');
if (cartBtn) {
    cartBtn.addEventListener('click', () => {
        const sidebar = document.getElementById('cart-sidebar');
        if (sidebar) sidebar.classList.remove('translate-x-full');
    });
}

// ==========================================
// THANH TOÁN (CHECKOUT)
// ==========================================
const checkoutBtn = document.getElementById('checkout-btn');
if (checkoutBtn) {
    checkoutBtn.addEventListener('click', async () => {
        if (cart.length === 0) {
            alert('Giỏ hàng đang trống!');
            return;
        }

        const token = localStorage.getItem('token');
        if (!token) {
            alert('Bạn cần đăng nhập để thực hiện đặt hàng!');
            window.location.href = 'login.html';
            return;
        }

        // FIX LỖI 422: Thêm user_id giả bằng 0 để chiều lòng FastAPI Schema
        const orderData = {
            user_id: 0, 
            items: cart.map(item => ({
                product_id: item.id || item.product_id,
                quantity: item.quantity
            }))
        };

        try {
            const response = await fetch('http://localhost:8000/api/orders/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(orderData)
            });

            const data = await response.json();
            
            if (response.ok) {
                alert('🎉 Đặt hàng thành công! Mã đơn: ' + data.order_id);
                cart = []; // Xóa trắng giỏ hàng
                updateCartUI(); // Cập nhật lại giao diện
                
                const sidebar = document.getElementById('cart-sidebar');
                if (sidebar) sidebar.classList.add('translate-x-full'); // Đóng sidebar
                
                loadProducts(); // Load lại sản phẩm để thấy kho tụt
            } else {
                // FIX LỖI OBJECT: Bắt chính xác lỗi mảng (Array) của FastAPI 422
                if (Array.isArray(data.detail)) {
                    alert('Lỗi dữ liệu: Vui lòng kiểm tra lại giỏ hàng của bạn.');
                    console.error("Chi tiết lỗi 422:", data.detail);
                } else {
                    alert(data.detail || 'Lỗi đặt hàng không xác định.');
                }
            }
        } catch (error) {
            console.error('Lỗi khi đặt hàng:', error);
            alert('Lỗi kết nối đến máy chủ. Không thể đặt hàng.');
        }
    });
}