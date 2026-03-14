let cart = [];

document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    updateCartUI(); 
    
    // Hiển thị thông tin người dùng
    const userStr = localStorage.getItem('user');
    const userInfoDiv = document.getElementById('user-info');
    if (userStr && userInfoDiv) {
        const user = JSON.parse(userStr);
        userInfoDiv.innerHTML = `Xin chào, <b class="text-blue-600">${user.full_name || user.email}</b>`;
    }
});

// TẢI DANH SÁCH SẢN PHẨM & DROPDOWN BIẾN THỂ
async function loadProducts() {
    try {
        const response = await fetch('http://localhost:8000/api/products/');
        const products = await response.json();
        
        const availableGrid = document.getElementById('product-grid'); 
        const outOfStockGrid = document.getElementById('outofstock-grid') || document.querySelector('#section-outofstock .grid');

        if (availableGrid) availableGrid.innerHTML = '';
        if (outOfStockGrid) outOfStockGrid.innerHTML = '';

        products.forEach(p => {
            if (!p.variants || p.variants.length === 0) return;

            let optionsHTML = '';
            p.variants.forEach(v => {
                optionsHTML += `<option value="${v.variant_id}" data-price="${v.price}" data-stock="${v.cached_stock}" data-name="${p.name} (${v.size}/${v.color})">
                                    Size: ${v.size} - Màu: ${v.color}
                                </option>`;
            });

            const defVar = p.variants[0];
            const imageTag = p.image_url 
                ? `<img src="${p.image_url}" alt="${p.name}" class="w-full h-48 object-cover rounded-md mb-4 shadow-sm">`
                : `<div class="w-full h-48 bg-gray-100 rounded-md mb-4 flex items-center justify-center text-gray-400">No Image</div>`;
            
            const productCard = `
                <div class="border p-4 rounded-lg shadow-sm hover:shadow-md transition bg-white flex flex-col">
                    ${imageTag}
                    <h3 class="font-bold text-lg text-gray-800">${p.name}</h3>
                    
                    <select id="select-${p.id}" class="mt-2 mb-1 border-gray-300 rounded text-sm bg-gray-50 focus:ring-blue-500" onchange="changeVariant('${p.id}')">
                        ${optionsHTML}
                    </select>

                    <p id="price-${p.id}" class="text-red-500 font-bold my-2 text-xl">${defVar.price.toLocaleString()} VNĐ</p>
                    <p class="text-gray-500 text-sm mb-4">Kho tạm: <span id="stock-${p.id}" class="font-mono font-bold ${defVar.cached_stock > 0 ? 'text-green-600' : 'text-red-500'}">${defVar.cached_stock}</span></p>
                    
                    <button id="btn-${p.id}" onclick="addToCart('${defVar.variant_id}', '${p.name} (${defVar.size}/${defVar.color})', ${defVar.price})" 
                            class="mt-auto font-semibold px-4 py-2 rounded-lg transition ${defVar.cached_stock > 0 ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}"
                            ${defVar.cached_stock <= 0 ? 'disabled' : ''}>
                        ${defVar.cached_stock > 0 ? 'Thêm vào giỏ' : 'Hết hàng'}
                    </button>
                </div>
            `;

            // Xét tổng kho để quyết định đưa vào lưới Còn Hàng hay Hết Hàng
            const totalStock = p.variants.reduce((sum, v) => sum + v.cached_stock, 0);
            if (totalStock > 0) {
                if (availableGrid) availableGrid.innerHTML += productCard;
            } else {
                if (outOfStockGrid) outOfStockGrid.innerHTML += productCard;
                else if (availableGrid) availableGrid.innerHTML += productCard; 
            }
        });
    } catch (error) {
        console.error('Lỗi tải sản phẩm:', error);
    }
}

// CẬP NHẬT UI KHI KHÁCH HÀNG CHỌN BIẾN THỂ KHÁC NHAU
window.changeVariant = function(productId) {
    const select = document.getElementById(`select-${productId}`);
    const selectedOption = select.options[select.selectedIndex];
    
    const price = selectedOption.getAttribute('data-price');
    const stock = parseInt(selectedOption.getAttribute('data-stock'));
    const name = selectedOption.getAttribute('data-name');
    const variantId = selectedOption.value;

    document.getElementById(`price-${productId}`).innerText = `${Number(price).toLocaleString()} VNĐ`;
    
    const stockSpan = document.getElementById(`stock-${productId}`);
    stockSpan.innerText = stock;
    stockSpan.className = `font-mono font-bold ${stock > 0 ? 'text-green-600' : 'text-red-500'}`;

    const btn = document.getElementById(`btn-${productId}`);
    btn.onclick = () => addToCart(variantId, name, Number(price));
    
    if (stock > 0) {
        btn.disabled = false;
        btn.className = 'mt-auto font-semibold px-4 py-2 rounded-lg transition bg-blue-600 text-white hover:bg-blue-700';
        btn.innerText = 'Thêm vào giỏ';
    } else {
        btn.disabled = true;
        btn.className = 'mt-auto font-semibold px-4 py-2 rounded-lg transition bg-gray-300 text-gray-500 cursor-not-allowed';
        btn.innerText = 'Hết hàng';
    }
}

// LOGIC GIỎ HÀNG
function addToCart(variantId, name, price) {
    const existing = cart.find(item => item.variant_id === variantId);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ variant_id: variantId, name: name, price: price, quantity: 1 });
    }
    
    updateCartUI();

    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar) sidebar.classList.remove('translate-x-full');
}

function increaseQuantity(variantId) {
    const item = cart.find(i => i.variant_id === variantId);
    if (item) {
        item.quantity += 1;
        updateCartUI();
    }
}

function decreaseQuantity(variantId) {
    const index = cart.findIndex(i => i.variant_id === variantId);
    if (index !== -1) {
        if (cart[index].quantity > 1) {
            cart[index].quantity -= 1;
        } else {
            cart.splice(index, 1);
        }
        updateCartUI();
    }
}

function updateCartUI() {
    const countSpan = document.getElementById('cart-count');
    if (countSpan) countSpan.innerText = cart.reduce((sum, item) => sum + item.quantity, 0);

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
        
        list.innerHTML += `
            <div class="flex justify-between items-center border-b border-gray-100 py-4">
                <div class="flex-1 pr-4">
                    <h4 class="font-semibold text-gray-800 text-sm leading-tight">${item.name}</h4>
                    <p class="text-red-500 font-bold text-sm mt-1">${item.price.toLocaleString()} đ</p>
                </div>
                <div class="flex items-center gap-3 bg-gray-50 px-2 py-1 rounded-lg border border-gray-200">
                    <button onclick="decreaseQuantity('${item.variant_id}')" class="text-gray-500 hover:text-red-500 font-bold px-1 transition">-</button>
                    <span class="w-6 text-center text-sm font-semibold">${item.quantity}</span>
                    <button onclick="increaseQuantity('${item.variant_id}')" class="text-gray-500 hover:text-green-600 font-bold px-1 transition">+</button>
                </div>
            </div>
        `;
    });

    const totalDiv = document.getElementById('cart-total');
    if (totalDiv) totalDiv.innerText = `${total.toLocaleString()} VNĐ`;
}

// ĐIỀU KHIỂN ĐÓNG MỞ GIỎ HÀNG
const closeCartBtn = document.getElementById('close-cart');
if (closeCartBtn) {
    closeCartBtn.addEventListener('click', () => {
        const sidebar = document.getElementById('cart-sidebar');
        if (sidebar) sidebar.classList.add('translate-x-full');
    });
}

const cartBtn = document.getElementById('cart-btn');
if (cartBtn) {
    cartBtn.addEventListener('click', () => {
        const sidebar = document.getElementById('cart-sidebar');
        if (sidebar) sidebar.classList.remove('translate-x-full');
    });
}

// THANH TOÁN ĐƠN HÀNG (API NHẬN VARIANT_ID)
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

        const orderData = {
            user_id: 0, 
            items: cart.map(item => ({
                variant_id: item.variant_id,
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
                cart = []; 
                updateCartUI(); 
                
                const sidebar = document.getElementById('cart-sidebar');
                if (sidebar) sidebar.classList.add('translate-x-full');
                
                loadProducts(); 
            } else {
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