const API_URL = "http://localhost:8000/api";
let cart = [];

// 1. Lấy danh sách sản phẩm từ Backend
async function fetchProducts() {
    try {
        const res = await fetch(`${API_URL}/products/`); // Thêm dấu / để khớp với router mới
        const products = await res.json();
        renderProducts(products);
    } catch (err) {
        document.getElementById('product-grid').innerHTML = "Không thể kết nối Backend.";
        console.error("Lỗi:", err);
    }
}

// 2. Render sản phẩm ra HTML (Cập nhật để hiển thị ảnh)
function renderProducts(products) {
    const grid = document.getElementById('product-grid');
    grid.innerHTML = products.map(p => {
        // Kiểm tra nếu sản phẩm có image_url, nếu không dùng ảnh placeholder
        const displayImage = p.image_url ? p.image_url : "https://via.placeholder.com/300?text=No+Image";
        
        return `
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm transition-all hover:shadow-md">
            <div class="aspect-square bg-slate-100 dark:bg-slate-800 rounded-lg mb-4 flex items-center justify-center relative overflow-hidden">
                <img src="${displayImage}" alt="${p.name}" class="object-cover w-full h-full">
                
                ${p.cached_stock <= 0 ? 
                    '<div class="absolute inset-0 bg-black/60 flex items-center justify-center text-white font-bold rounded-lg text-sm">HẾT HÀNG</div>' 
                    : ''}
            </div>
            <h3 class="font-bold text-lg truncate">${p.name}</h3>
            <div class="flex justify-between items-center mt-2 mb-4">
                <span class="text-xl font-extrabold text-blue-600">$${p.price.toFixed(2)}</span>
                <span class="text-xs ${p.cached_stock < 5 ? 'text-red-500 font-bold' : 'text-slate-500'}">
                    ${p.cached_stock} in stock
                </span>
            </div>
            <button onclick="addToCart('${p.id}', '${p.name}', ${p.price})" 
                ${p.cached_stock <= 0 ? 'disabled' : ''}
                class="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed font-semibold">
                Add to Cart
            </button>
        </div>
    `}).join('');
}

// 3. Logic Giỏ hàng (Giữ nguyên)
function addToCart(id, name, price) {
    const item = cart.find(i => i.product_id === id);
    if (item) {
        item.quantity += 1;
    } else {
        cart.push({ product_id: id, name, price, quantity: 1 });
    }
    updateCartUI();
}

function updateCartUI() {
    const cartList = document.getElementById('cart-items');
    const totalEl = document.getElementById('total-price');
    const badge = document.getElementById('cart-count-badge');
    
    if (cart.length === 0) {
        cartList.innerHTML = '<p class="text-sm text-slate-500 italic text-center">Your bag is empty.</p>';
        totalEl.innerText = "$0.00";
        badge.innerText = "0";
        return;
    }

    cartList.innerHTML = cart.map(i => `
        <div class="flex justify-between items-center text-sm bg-slate-50 dark:bg-slate-800 p-2 rounded-lg">
            <div class="flex flex-col">
                <span class="font-medium">${i.name}</span>
                <span class="text-xs text-slate-500">Qty: ${i.quantity}</span>
            </div>
            <span class="font-bold text-blue-600">$${(i.price * i.quantity).toFixed(2)}</span>
        </div>
    `).join('');

    const total = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    totalEl.innerText = `$${total.toFixed(2)}`;
    badge.innerText = cart.reduce((sum, i) => sum + i.quantity, 0);
}

// 4. Gửi đơn hàng tới Backend (Giữ nguyên)
document.getElementById('checkout-btn').addEventListener('click', async () => {
    if (cart.length === 0) return;
    
    const orderData = {
        user_id: 1, 
        items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity }))
    };

    try {
        const res = await fetch(`${API_URL}/orders/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        if (res.ok) {
            alert("Đặt hàng thành công!");
            cart = [];
            updateCartUI();
            fetchProducts(); 
        } else {
            const error = await res.json();
            alert("Lỗi: " + (error.detail || "Không thể đặt hàng"));
        }
    } catch (err) {
        alert("Lỗi kết nối máy chủ.");
    }
});

document.addEventListener('DOMContentLoaded', fetchProducts);