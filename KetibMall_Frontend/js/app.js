// --- 1. CẤU HÌNH & TRẠNG THÁI ---
const API_BASE = "http://localhost:8000/api";
let cart = [];

// --- 2. KIỂM TRA ĐĂNG NHẬP (AUTH GUARD) ---
(function init() {
    const userStr = localStorage.getItem('ketib_user');
    if (!userStr) {
        window.location.href = "login.html";
        return;
    }
    const userData = JSON.parse(userStr);
    const display = document.getElementById('user-display');
    if (display) {
        display.innerHTML = `
            <div class="flex items-center gap-4">
                <span class="text-sm font-medium text-slate-700">Chào, ${userData.full_name}</span>
                <button onclick="logout()" class="text-xs font-bold text-red-500 hover:bg-red-50 px-2 py-1 rounded transition-all">Đăng xuất</button>
            </div>
        `;
    }
})();

function logout() {
    localStorage.removeItem('ketib_user');
    window.location.href = "login.html";
}

// --- 3. TẢI VÀ HIỂN THỊ SẢN PHẨM ---
async function fetchProducts() {
    const grid = document.getElementById('product-grid');
    try {
        const response = await fetch(`${API_BASE}/products/`);
        const products = await response.json();
        
        grid.innerHTML = products.map(product => `
            <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div class="aspect-square bg-slate-50">
                    <img src="${product.image_url || ''}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/300'">
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-slate-800">${product.name}</h3>
                    <p class="text-slate-500 text-xs mb-3 line-clamp-2">${product.description || ''}</p>
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-primary">${product.price.toLocaleString()}đ</span>
                        <button onclick="addToCart('${product.id}', '${product.name}', ${product.price})" 
                                class="p-2 bg-primary text-white rounded-lg hover:bg-blue-700 transition-colors">
                            <span class="material-symbols-outlined text-sm">add_shopping_cart</span>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) { 
        console.error("Lỗi fetch sản phẩm:", e); 
    }
}

// --- 4. QUẢN LÝ GIỎ HÀNG ---
function addToCart(id, name, price) {
    const existing = cart.find(item => item.product_id === id);
    if (existing) {
        existing.quantity += 1;
    } else {
        // Cấu trúc khớp với phần tử trong mảng items của API
        cart.push({ product_id: id, name: name, price: price, quantity: 1 });
    }
    updateCartUI();
    // Tự động mở sidebar giỏ hàng nếu đang đóng
    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar && sidebar.classList.contains('translate-x-full')) {
        toggleCart();
    }
}

function updateCartUI() {
    const itemsContainer = document.getElementById('cart-items');
    const totalDisplay = document.getElementById('cart-total');
    const countDisplay = document.getElementById('cart-count');
    
    const totalQty = cart.reduce((s, i) => s + i.quantity, 0);
    const totalPrice = cart.reduce((s, i) => s + (i.price * i.quantity), 0);

    if (countDisplay) countDisplay.innerText = totalQty;
    if (totalDisplay) totalDisplay.innerText = totalPrice.toLocaleString() + 'đ';
    
    if (itemsContainer) {
        itemsContainer.innerHTML = cart.map(i => `
            <div class="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div class="text-sm">
                    <p class="font-bold text-slate-800">${i.name}</p>
                    <p class="text-slate-500 text-xs">${i.quantity} x ${i.price.toLocaleString()}đ</p>
                </div>
                <span class="font-bold text-primary">${(i.price * i.quantity).toLocaleString()}đ</span>
            </div>
        `).join('');
    }
}

// --- 5. THANH TOÁN (GỬI DỮ LIỆU ĐÚNG CẤU TRÚC API) ---
async function handleCheckout() {
    if (cart.length === 0) return alert("Giỏ hàng của bạn đang trống!");
    
    const userStr = localStorage.getItem('ketib_user');
    const userData = JSON.parse(userStr);
    
    // Xây dựng Object đúng cấu trúc yêu cầu
    const orderData = {
        user_id: parseInt(userData.id),
        items: cart.map(i => ({
            product_id: String(i.product_id),
            quantity: parseInt(i.quantity)
        }))
    };

    try {
        const btn = document.getElementById('checkout-btn');
        btn.disabled = true;
        btn.innerText = "Đang xử lý...";

        const response = await fetch(`${API_BASE}/orders/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (response.ok) {
            alert("Đặt hàng thành công!");
            cart = []; 
            updateCartUI(); 
            if (typeof toggleCart === 'function') toggleCart(); 
            fetchProducts(); // Cập nhật lại số lượng tồn kho trên giao diện
        } else {
            alert("Lỗi đặt hàng: " + (result.detail || "Vui lòng thử lại sau."));
        }
    } catch (e) { 
        console.error("Lỗi kết nối API orders:", e);
        alert("Không thể kết nối tới máy chủ."); 
    } finally {
        const btn = document.getElementById('checkout-btn');
        btn.disabled = false;
        btn.innerText = "Thanh toán ngay";
    }
}

// --- 6. KHỞI CHẠY ---
document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.onclick = handleCheckout;
    }
});