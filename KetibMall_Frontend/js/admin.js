document.addEventListener('DOMContentLoaded', () => {
    // KIỂM TRA QUYỀN TRUY CẬP
    const authMessageDiv = document.getElementById('auth-message');
    const adminContentDiv = document.getElementById('admin-content');

    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    
    if (!token || !userStr) {
        authMessageDiv.innerHTML = `
            <div class="bg-white p-8 rounded-lg shadow-md text-center max-w-md w-full mx-4">
                <svg class="w-16 h-16 text-yellow-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                <h2 class="text-2xl font-bold mb-2 text-gray-800">Truy cập bị từ chối</h2>
                <p class="mb-6 text-gray-600">Vui lòng đăng nhập để tiếp tục!</p>
                <a href="login.html" class="inline-block bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-2 rounded transition-colors">Đăng nhập</a>
            </div>
        `;
        authMessageDiv.classList.remove('hidden');
        return;
    }

    const user = JSON.parse(userStr);
    
    if (user.role !== 'admin') {
        authMessageDiv.innerHTML = `
            <div class="bg-white p-8 rounded-lg shadow-md text-center max-w-md w-full mx-4">
                <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                <h2 class="text-2xl font-bold mb-2 text-gray-800">Lỗi 403</h2>
                <p class="mb-6 text-gray-600">Bạn không có quyền truy cập vào trang Quản trị.</p>
                <a href="app.html" class="inline-block bg-red-500 hover:bg-red-600 text-white font-semibold px-8 py-2 rounded transition-colors">Về trang chủ</a>
            </div>
        `;
        authMessageDiv.classList.remove('hidden');
        return;
    }

    // Nếu là Admin -> Hiện giao diện
    adminContentDiv.classList.remove('hidden');
    
    const userInfoDiv = document.getElementById('user-info');
    if (userInfoDiv) {
        userInfoDiv.innerHTML = `Xin chào Admin: <span class="text-blue-600">${user.full_name || user.email}</span>`;
    }

    // Load dữ liệu
    loadProducts();
    loadOrders();
});

function addLog(message, isError = false) {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;
    const logItem = document.createElement('div');
    const time = new Date().toLocaleTimeString();
    
    logItem.className = isError ? 'text-red-500 font-semibold' : 'text-green-600';
    logItem.innerHTML = `<span class="text-gray-400">[${time}]</span> ${message}`;
    
    logContainer.prepend(logItem);
}

// TẢI SẢN PHẨM & BIẾN THỂ TỪ APP VÀ INVENTORY
async function loadProducts() {
    const tbody = document.getElementById('product-list');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400 italic">Đang tải dữ liệu...</td></tr>';

    try {
        const resApp = await fetch('http://localhost:8080/api/products/');
        const products = await resApp.json();

        if (products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400">Chưa có sản phẩm nào.</td></tr>';
            return;
        }

        let html = '';
        for (const p of products) {
            for (const v of p.variants) {
                let actualStock = 0;
                try {
                    const resInv = await fetch(`http://localhost:8080/api/inventory/status/${v.variant_id}`);
                    if (resInv.ok) {
                        const invData = await resInv.json();
                        actualStock = invData.stock ?? 0;
                    }
                } catch (e) { }

                html += `
                    <tr class="hover:bg-slate-50 transition-colors border-b">
                        <td class="px-6 py-4 font-bold text-primary font-mono">${v.variant_id}</td>
                        <td class="px-6 py-4 flex items-center gap-3">
                            ${p.image_url ? `<img src="${p.image_url}" class="w-8 h-8 rounded object-cover">` : ''}
                            ${p.name}
                        </td>
                        <td class="px-6 py-4"><span class="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded font-bold">${v.size} / ${v.color}</span></td>
                        <td class="px-6 py-4">${v.price.toLocaleString()}đ</td>
                        <td class="px-6 py-4 text-center font-mono font-bold text-lg ${actualStock > 0 ? 'text-green-600' : 'text-red-500'}">
                            ${actualStock}
                        </td>
                    </tr>
                `;
            }
        }
        tbody.innerHTML = html;
        addLog("[HỆ THỐNG] Đã làm mới dữ liệu Bảng điều khiển.");
    } catch (error) {
        console.error('Lỗi tải sản phẩm:', error);
        addLog("Lỗi đồng bộ dữ liệu giữa các Service.", true);
    }
}

// FORM 1: THÊM SẢN PHẨM & BIẾN THỂ
const productForm = document.getElementById('product-form');
if (productForm) {
    productForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const token = localStorage.getItem('token');
        const prodId = document.getElementById('product_id').value;
        const prodName = document.getElementById('product_name').value;
        
        const variants = [];
        document.querySelectorAll('.variant-row').forEach(row => {
            variants.push({
                size: row.querySelector('.var-size').value,
                color: row.querySelector('.var-color').value,
                price: parseFloat(row.querySelector('.var-price').value)
            });
        });

        const productData = {
            id: prodId,
            name: prodName,
            variants: variants
        };

        const formData = new FormData();
        formData.append('product_data', JSON.stringify(productData)); 
        
        const imageFile = document.getElementById('product_image').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        try {
            const response = await fetch('http://localhost:8080/api/products/', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                addLog(`[APP] Khai báo thành công SP mới: ${prodId} kèm ${variants.length} phân loại.`);
                loadProducts(); 
                productForm.reset();
                
                if (variants.length > 0) {
                    const firstVariantId = `${prodId}-${variants[0].size}-${variants[0].color}`.toUpperCase();
                    document.getElementById('import_product_id').value = firstVariantId;
                }
                
                document.getElementById('image-preview-el').classList.add('hidden');
                document.getElementById('preview-placeholder').classList.remove('hidden');
                
                // Giữ lại 1 ô variant trống
                document.getElementById('variants-container').innerHTML = `
                    <div class="variant-row flex gap-2">
                        <input type="text" placeholder="Size (S,M..)" class="var-size w-1/3 border-gray-300 rounded text-sm" required>
                        <input type="text" placeholder="Màu (Đỏ..)" class="var-color w-1/3 border-gray-300 rounded text-sm" required>
                        <input type="number" placeholder="Giá (VNĐ)" class="var-price w-1/3 border-gray-300 rounded text-sm" required>
                    </div>
                `;
            } else {
                addLog(`[LỖI APP] ${data.detail || 'Không thể tạo sản phẩm'}`, true);
            }
        } catch (error) {
            addLog("CRITICAL: Lỗi kết nối tới App Service", true);
        }
    });
}

// FORM 2: NHẬP KHO (BẰNG VARIANT_ID)
const importForm = document.getElementById('import-form');
if (importForm) {
    importForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const token = localStorage.getItem('token');
        const variantId = document.getElementById('import_product_id').value;
        const quantity = document.getElementById('import_quantity').value;

        try {
            const response = await fetch('http://localhost:8080/api/inventory/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ variant_id: variantId, quantity: parseInt(quantity) })
            });

            const data = await response.json();
            if (response.ok) {
                addLog(`[KHO] Nhập thêm ${quantity} đơn vị cho mã ${variantId} thành công.`);
                importForm.reset();
                setTimeout(() => { loadProducts(); }, 1000); 
            } else {
                addLog(`[LỖI KHO] Không thể nhập hàng cho mã ${variantId}`, true);
            }
        } catch (error) {
            addLog("CRITICAL: Lỗi kết nối tới Inventory Service (Port 8001)", true);
        }
    });
}

// TẢI VÀ QUẢN LÝ ĐƠN HÀNG
async function loadOrders() {
    const tbody = document.getElementById('order-list');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400 italic">Đang tải đơn hàng...</td></tr>';

    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://localhost:8080/api/orders/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error("Không thể tải danh sách");
        const orders = await response.json();

        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400">Chưa có đơn hàng nào trong hệ thống.</td></tr>';
            return;
        }

        let html = '';
        const statusColors = {
            'PENDING': 'bg-yellow-100 text-yellow-800',
            'PAID': 'bg-blue-100 text-blue-800',
            'SHIPPING': 'bg-purple-100 text-purple-800',
            'COMPLETED': 'bg-green-100 text-green-800',
            'CANCELED': 'bg-red-100 text-red-800'
        };

        orders.forEach(o => {
            const colorClass = statusColors[o.status] || 'bg-gray-100 text-gray-800';
            html += `
                <tr class="hover:bg-slate-50 transition-colors border-b">
                    <td class="px-6 py-4 font-bold text-gray-700">${o.id}</td>
                    <td class="px-6 py-4 font-mono">User #${o.user_id}</td>
                    <td class="px-6 py-4">${o.items_count} mặt hàng</td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 text-xs font-semibold rounded-full ${colorClass}">
                            ${o.status}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-center">
                        <select onchange="updateOrderStatus('${o.id}', this.value)" 
                            class="text-sm border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary p-2">
                            <option value="" disabled selected>Đổi trạng thái...</option>
                            <option value="PENDING">PENDING (Chờ xử lý)</option>
                            <option value="PAID">PAID (Đã thanh toán)</option>
                            <option value="SHIPPING">SHIPPING (Đang giao)</option>
                            <option value="COMPLETED">COMPLETED (Thành công)</option>
                            <option value="CANCELED">CANCELED (Hủy đơn)</option>
                        </select>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
        addLog("[ĐƠN HÀNG] Đã tải mới danh sách đơn mua.");
    } catch (error) {
        console.error('Lỗi tải đơn hàng:', error);
        addLog("Lỗi khi kết nối lấy dữ liệu đơn hàng.", true);
    }
}

async function updateOrderStatus(orderId, newStatus) {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`http://localhost:8080/api/orders/${orderId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
            addLog(`[ĐƠN HÀNG] Đã cập nhật đơn ${orderId} thành ${newStatus}`);
            loadOrders(); 
        } else {
            const data = await response.json();
            addLog(`[LỖI CẬP NHẬT] ${data.detail}`, true);
            loadOrders(); 
        }
    } catch (error) {
        console.error('Lỗi cập nhật trạng thái:', error);
        addLog("Lỗi kết nối khi cập nhật đơn hàng.", true);
    }
}