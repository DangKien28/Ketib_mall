let globalProducts = [];

document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadCartUI(); // Tải giỏ hàng từ Redis ngay khi mở trang
    
    // Hiển thị thông tin người dùng
    const userStr = localStorage.getItem('user');
    const userInfoDiv = document.getElementById('user-info');
    if (userStr && userInfoDiv) {
        const user = JSON.parse(userStr);
        userInfoDiv.innerHTML = `Xin chào, <b class="text-blue-600">${user.full_name || user.email}</b>`;
    }
});

// ==========================================
// 1. TẢI VÀ HIỂN THỊ SẢN PHẨM (CÓ TÌM KIẾM)
// ==========================================
async function loadProducts() {
    try {
        const response = await fetch('http://localhost:8080/api/products/');
        const products = await response.json();
        
        globalProducts = products; // Lưu lại dữ liệu gốc
        renderProducts(globalProducts); // Vẽ toàn bộ sản phẩm ra màn hình
    } catch (error) {
        console.error('Lỗi tải sản phẩm:', error);
    }
}

function renderProducts(productsToDisplay) {
    const availableGrid = document.getElementById('product-grid'); 
    const outOfStockGrid = document.getElementById('outofstock-grid') || document.querySelector('#section-outofstock .grid');

    if (availableGrid) availableGrid.innerHTML = '';
    if (outOfStockGrid) outOfStockGrid.innerHTML = '';

    if (productsToDisplay.length === 0) {
        if (availableGrid) availableGrid.innerHTML = `<div class="col-span-full text-center text-gray-500 py-10">Không tìm thấy sản phẩm nào phù hợp!</div>`;
        return;
    }

    productsToDisplay.forEach(p => {
        if (!p.variants || p.variants.length === 0) return;

        let optionsHTML = '';
        p.variants.forEach(v => {
            optionsHTML += `<option value="${v.variant_id}" data-price="${v.price}" data-stock="${v.cached_stock}">
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
                
                <button id="btn-${p.id}" onclick="addToCart('${defVar.variant_id}', 1)" 
                        class="mt-auto font-semibold px-4 py-2 rounded-lg transition ${defVar.cached_stock > 0 ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}"
                        ${defVar.cached_stock <= 0 ? 'disabled' : ''}>
                    ${defVar.cached_stock > 0 ? 'Thêm vào giỏ' : 'Hết hàng'}
                </button>
            </div>
        `;

        const totalStock = p.variants.reduce((sum, v) => sum + v.cached_stock, 0);
        if (totalStock > 0) {
            if (availableGrid) availableGrid.innerHTML += productCard;
        } else {
            if (outOfStockGrid) outOfStockGrid.innerHTML += productCard;
            else if (availableGrid) availableGrid.innerHTML += productCard; 
        }
    });
}

// Hàm xử lý tìm kiếm (Được gọi mỗi khi gõ phím)
window.searchProducts = function() {
    const keyword = document.getElementById('search-input').value.toLowerCase().trim();
    
    // Lọc các sản phẩm có tên chứa từ khóa
    const filteredProducts = globalProducts.filter(p => 
        p.name.toLowerCase().includes(keyword)
    );
    
    // Vẽ lại màn hình với danh sách đã lọc
    renderProducts(filteredProducts);
}

window.changeVariant = function(productId) {
    const select = document.getElementById(`select-${productId}`);
    const selectedOption = select.options[select.selectedIndex];
    
    const price = selectedOption.getAttribute('data-price');
    const stock = parseInt(selectedOption.getAttribute('data-stock'));
    const variantId = selectedOption.value;

    document.getElementById(`price-${productId}`).innerText = `${Number(price).toLocaleString()} VNĐ`;
    
    const stockSpan = document.getElementById(`stock-${productId}`);
    stockSpan.innerText = stock;
    stockSpan.className = `font-mono font-bold ${stock > 0 ? 'text-green-600' : 'text-red-500'}`;

    const btn = document.getElementById(`btn-${productId}`);
    btn.onclick = () => addToCart(variantId, 1);
    
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

// ==========================================
// 2. LOGIC GIỎ HÀNG (DÙNG API REDIS)
// ==========================================
async function addToCart(variantId, quantity, isSilent = false) {
    const token = localStorage.getItem('token');
    if (!token) {
        alert("Bạn cần đăng nhập để thêm hàng vào giỏ nhé!");
        window.location.href = "login.html";
        return;
    }

    try {
        const response = await fetch('http://localhost:8080/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ variant_id: variantId, quantity: quantity })
        });

        if (response.ok) {
            // Chỉ hiện thông báo khi số lượng > 0 VÀ không bị yêu cầu im lặng (isSilent = false)
            if (quantity > 0 && !isSilent) {
                alert("Đã thêm sản phẩm vào giỏ hàng thành công!");
            }
            loadCartUI(); // Cập nhật lại giao diện giỏ hàng
        } else {
            const data = await response.json();
            alert("Lỗi: " + (data.detail || "Không thể cập nhật giỏ hàng."));
        }
    } catch (error) {
        console.error("Lỗi kết nối:", error);
    }
}

// Hàm dùng cho nút [+] và [-] trong thanh sidebar Giỏ hàng
window.updateCartQuantity = function(variantId, change) {
    // Truyền tham số true vào cuối để báo cho hàm addToCart biết: "Hãy chạy ngầm, đừng hiện alert nhé!"
    addToCart(variantId, change, true); 
}

// Tải Giỏ hàng từ Backend và vẽ ra giao diện
async function loadCartUI() {
    const token = localStorage.getItem('token');
    const countSpan = document.getElementById('cart-count');
    const list = document.getElementById('cart-items');
    const totalDiv = document.getElementById('cart-total');

    if (!token) {
        if(countSpan) countSpan.innerText = '0';
        if(list) list.innerHTML = '<div class="text-center text-gray-500 mt-10">Vui lòng đăng nhập để xem giỏ hàng.</div>';
        if(totalDiv) totalDiv.innerText = '0 VNĐ';
        return;
    }

    try {
        const response = await fetch('http://localhost:8080/api/cart/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        const cartData = data.cart || {}; // Lấy cái hộp đồ trong Redis ra
        
        let totalItems = 0;
        let totalPrice = 0;
        let html = '';
        const cartKeys = Object.keys(cartData);

        if (cartKeys.length === 0) {
            if(list) list.innerHTML = '<div class="text-center text-gray-500 mt-10">Giỏ hàng của bạn đang trống.</div>';
            if(totalDiv) totalDiv.innerText = '0 VNĐ';
            if(countSpan) countSpan.innerText = '0';
            return;
        }

        // Lắp ráp thông tin
        cartKeys.forEach(variantId => {
            const qty = parseInt(cartData[variantId]);
            totalItems += qty;

            // Tìm Tên và Giá của sản phẩm từ globalProducts
            let itemName = variantId;
            let itemPrice = 0;
            
            globalProducts.forEach(p => {
                const variant = p.variants.find(v => v.variant_id === variantId);
                if (variant) {
                    itemName = `${p.name} (${variant.size}/${variant.color})`;
                    itemPrice = variant.price;
                }
            });

            totalPrice += itemPrice * qty;

            html += `
                <div class="flex justify-between items-center border-b border-gray-100 py-4">
                    <div class="flex-1 pr-4">
                        <h4 class="font-semibold text-gray-800 text-sm leading-tight">${itemName}</h4>
                        <p class="text-red-500 font-bold text-sm mt-1">${itemPrice.toLocaleString()} đ</p>
                    </div>
                    <div class="flex items-center gap-3 bg-gray-50 px-2 py-1 rounded-lg border border-gray-200">
                        <button onclick="updateCartQuantity('${variantId}', -1)" class="text-gray-500 hover:text-red-500 font-bold px-1 transition">-</button>
                        <span class="w-6 text-center text-sm font-semibold">${qty}</span>
                        <button onclick="updateCartQuantity('${variantId}', 1)" class="text-gray-500 hover:text-green-600 font-bold px-1 transition">+</button>
                    </div>
                </div>
            `;
        });

        if(list) list.innerHTML = html;
        if(totalDiv) totalDiv.innerText = `${totalPrice.toLocaleString()} VNĐ`;
        if(countSpan) countSpan.innerText = totalItems;

    } catch (error) {
        console.error("Lỗi tải giao diện giỏ hàng:", error);
    }
}

// ==========================================
// 3. ĐIỀU KHIỂN ĐÓNG MỞ GIỎ HÀNG & THANH TOÁN
// ==========================================
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

const checkoutBtn = document.getElementById('checkout-btn');
if (checkoutBtn) {
    checkoutBtn.addEventListener('click', async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Bạn cần đăng nhập để thực hiện đặt hàng!');
            window.location.href = 'login.html';
            return;
        }

        // Lấy dữ liệu Giỏ hàng mới nhất từ Redis trước khi thanh toán
        const cartRes = await fetch('http://localhost:8080/api/cart/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const cartData = await cartRes.json();
        
        if (!cartData.cart || Object.keys(cartData.cart).length === 0) {
            alert('Giỏ hàng đang trống!');
            return;
        }

        // Đóng gói theo chuẩn API Thanh toán
        const items = Object.keys(cartData.cart).map(vId => ({
            variant_id: vId,
            quantity: parseInt(cartData.cart[vId])
        }));

        try {
            const response = await fetch('http://localhost:8080/api/orders/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ user_id: 0, items: items }) 
            });

            const data = await response.json();
            
            if (response.ok) {
                // Xóa các sản phẩm khỏi giỏ hàng
                for (let vId of items.map(i => i.variant_id)) {
                    await fetch(`http://localhost:8080/api/cart/remove/${vId}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                }
                
                // Chuyển hướng trình duyệt sang trang thanh toán Stripe
                window.location.href = data.checkout_url;
                
            } else {
                alert('Lỗi đặt hàng: ' + (data.detail || 'Không xác định'));
            }
        } catch (error) {
            console.error('Lỗi khi đặt hàng:', error);
            alert('Lỗi kết nối đến máy chủ. Không thể đặt hàng.');
        }
    });
}