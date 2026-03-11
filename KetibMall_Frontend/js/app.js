// --- 1. CẤU HÌNH & TRẠNG THÁI ---
const API_BASE = "http://localhost:8000/api";
let cart = [];

// --- 2. KHỞI TẠO HỆ THỐNG ---
(function init() {
    const userStr = localStorage.getItem('ketib_user');
    // Kiểm tra đăng nhập (trừ trang login/register)
    if (!userStr && !window.location.href.includes('login.html') && !window.location.href.includes('register.html')) {
        window.location.href = "login.html";
        return;
    }

    if (userStr) {
        const userData = JSON.parse(userStr);
        const display = document.getElementById('user-display');
        if (display) {
            display.innerHTML = `
                <div class="flex items-center gap-4">
                    <span class="text-sm font-medium text-slate-700">Chào, ${userData.full_name}</span>
                    <button onclick="logout()" class="text-xs font-bold text-red-500 hover:bg-red-50 px-2 py-1 rounded transition-all">Đăng xuất</button>
                </div>`;
        }
    }

    // Tải giỏ hàng từ LocalStorage để đồng bộ giữa các trang
    const savedCart = localStorage.getItem('ketib_cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
    }
})();

function logout() {
    localStorage.removeItem('ketib_user');
    localStorage.removeItem('ketib_cart');
    window.location.href = "login.html";
}

// --- 3. TẢI VÀ PHÂN LOẠI SẢN PHẨM ---
async function fetchProducts() {
    const gridAvailable = document.getElementById('product-grid');
    const gridOutOfStock = document.getElementById('product-grid-out');
    const outSection = document.getElementById('section-outofstock');
    
    if (!gridAvailable) return; // Nếu không ở trang app.html thì dừng

    try {
        const response = await fetch(`${API_BASE}/products/`);
        const products = await response.json();
        
        const available = products.filter(p => p.cached_stock > 0);
        const outOfStock = products.filter(p => p.cached_stock <= 0);

        const renderItem = (p, isOut) => `
            <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden relative transition-all hover:shadow-md ${isOut ? 'opacity-70' : ''}">
                <a href="detail.html?id=${p.id}" class="block cursor-pointer">
                    <div class="absolute top-2 right-2 z-10 ${isOut ? 'bg-red-500' : 'bg-black/60'} backdrop-blur-sm text-white text-[10px] px-2 py-1 rounded-md font-bold">
                        ${isOut ? 'HẾT HÀNG' : 'Kho: ' + p.cached_stock}
                    </div>
                    <div class="aspect-square bg-slate-50 overflow-hidden">
                        <img src="${p.image_url || ''}" class="w-full h-full object-cover transition-all ${isOut ? 'grayscale contrast-75' : ''}" 
                             onerror="this.onerror=null; this.src='http://localhost:8000/static/logo_TK.png';">
                    </div>
                    <div class="p-4">
                        <h3 class="font-bold text-slate-800 line-clamp-1 ${isOut ? 'text-slate-400' : ''}">${p.name}</h3>
                    </div>
                </a>
                <div class="px-4 pb-4">
                    <div class="flex items-center justify-between pt-2 border-t border-slate-50">
                        <span class="font-bold ${isOut ? 'text-slate-400' : 'text-primary'}">${p.price.toLocaleString()}đ</span>
                        <button onclick="${isOut ? '' : `addToCart('${p.id}', '${p.name}', ${p.price})`}"
                                ${isOut ? 'disabled' : ''}
                                class="p-2 rounded-lg transition-colors ${isOut ? 'bg-slate-200 text-slate-400 cursor-not-allowed' : 'bg-primary text-white hover:bg-blue-700'}">
                            <span class="material-symbols-outlined text-sm">${isOut ? 'block' : 'add_shopping_cart'}</span>
                        </button>
                    </div>
                </div>
            </div>`;

        // Render khu vực còn hàng
        gridAvailable.innerHTML = available.length > 0 
            ? available.map(p => renderItem(p, false)).join('') 
            : '<p class="col-span-full text-center text-slate-400 py-10">Không có sản phẩm nào sẵn có.</p>';
        
        // Render khu vực hết hàng
        if (gridOutOfStock) {
            gridOutOfStock.innerHTML = outOfStock.map(p => renderItem(p, true)).join('');
            if (outSection) outSection.style.display = outOfStock.length > 0 ? 'block' : 'none';
        }

    } catch (e) { console.error("Lỗi fetch sản phẩm:", e); }
}

// --- 4. QUẢN LÝ GIỎ HÀNG ---

function addToCart(id, name, price) {
    const existing = cart.find(i => i.product_id === id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ product_id: id, name: name, price: price, quantity: 1 });
    }
    updateCartUI();
    
    // Mở sidebar nếu đang ở trang app.html
    const sb = document.getElementById('cart-sidebar');
    if (sb && sb.classList.contains('translate-x-full')) toggleCart();
}

function updateQuantity(id, val) {
    const qty = parseInt(val);
    if (isNaN(qty) || qty < 1) return;
    const item = cart.find(i => i.product_id === id);
    if (item) { 
        item.quantity = qty; 
        updateCartUI(); 
    }
}

function removeFromCart(id) {
    cart = cart.filter(i => i.product_id !== id);
    updateCartUI();
}

function updateCartUI() {
    // Luôn lưu vào LocalStorage để đồng bộ trang detail.html
    localStorage.setItem('ketib_cart', JSON.stringify(cart));

    const items = document.getElementById('cart-items');
    const total = document.getElementById('cart-total');
    const count = document.getElementById('cart-count');
    
    const totalQty = cart.reduce((s, i) => s + i.quantity, 0);
    const totalPrice = cart.reduce((s, i) => s + (i.price * i.quantity), 0);

    if (count) count.innerText = totalQty;
    if (total) total.innerText = totalPrice.toLocaleString() + 'đ';
    
    if (items) {
        if (cart.length === 0) {
            items.innerHTML = `
                <div class="flex flex-col items-center justify-center h-full opacity-30 py-20">
                    <span class="material-symbols-outlined text-6xl text-slate-400">remove_shopping_cart</span>
                    <p class="mt-4 text-sm font-medium text-slate-400">Giỏ hàng trống</p>
                </div>`;
            return;
        }

        items.innerHTML = cart.map(i => `
            <div class="bg-slate-800/50 p-4 rounded-2xl border border-slate-700/50 space-y-3">
                <div class="flex justify-between items-start">
                    <div class="flex-1 text-sm">
                        <p class="font-bold text-white line-clamp-1">${i.name}</p>
                        <p class="text-indigo-400 font-bold mt-1">${i.price.toLocaleString()}đ</p>
                    </div>
                    <button onclick="removeFromCart('${i.product_id}')" 
                            class="h-8 w-8 flex items-center justify-center rounded-full bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white transition-all">
                        <span class="material-symbols-outlined text-lg">delete</span>
                    </button>
                </div>
                <div class="flex items-center justify-between pt-2 border-t border-slate-700/50">
                    <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Số lượng</label>
                    <input type="number" value="${i.quantity}" min="1" 
                           onchange="updateQuantity('${i.product_id}', this.value)" 
                           class="w-12 bg-slate-900 border border-slate-700 rounded text-center text-white text-sm focus:outline-none">
                </div>
            </div>`).join('');
    }
}

// --- 5. THANH TOÁN ---
async function handleCheckout() {
    if (cart.length === 0) return alert("Giỏ hàng của bạn đang trống!");
    
    const userStr = localStorage.getItem('ketib_user');
    const userData = JSON.parse(userStr);
    
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

        const res = await fetch(`${API_BASE}/orders/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        if (res.ok) {
            alert("Đặt hàng thành công!");
            cart = []; 
            updateCartUI(); 
            if (typeof toggleCart === 'function') toggleCart(); 
            fetchProducts(); 
        } else {
            const err = await res.json();
            alert("Lỗi: " + (err.detail || "Thanh toán thất bại"));
        }
    } catch (e) { 
        alert("Lỗi kết nối máy chủ!"); 
    } finally {
        const btn = document.getElementById('checkout-btn');
        btn.disabled = false;
        btn.innerText = "Thanh toán ngay";
    }
}

// --- 6. KHỞI CHẠY ---
document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
    updateCartUI(); // Load lại giỏ hàng từ localStorage
    const btn = document.getElementById('checkout-btn');
    if (btn) btn.onclick = handleCheckout;
});