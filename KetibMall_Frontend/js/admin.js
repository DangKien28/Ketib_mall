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
    loadOrders(); // THÊM MỚI: Tải luôn danh sách đơn hàng khi mở trang
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

async function loadProducts() {
    const tbody = document.getElementById('product-list');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400 italic">Đang tải dữ liệu...</td></tr>';

    try {
        const resApp = await fetch('http://localhost:8000/api/products/');
        const products = await resApp.json();

        if (products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400">Chưa có sản phẩm nào.</td></tr>';
            return;
        }

        let html = '';
        for (const p of products) {
            let actualStock = 0;
            try {
                const resInv = await fetch(`http://localhost:8001/api/inventory/status/${p.id}`);
                const invData = await resInv.json();
                actualStock = invData.stock ?? 0;
            } catch (e) { 
                console.error(`Không lấy được stock cho ${p.id}`); 
            }

            html += `
                <tr class="hover:bg-slate-50 transition-colors border-b">
                    <td class="px-6 py-4 font-bold text-primary">${p.id}</td>
                    <td class="px-6 py-4">${p.name}</td>
                    <td class="px-6 py-4">${p.price.toLocaleString()}đ</td>
                    <td class="px-6 py-4 text-center font-mono font-bold text-lg ${actualStock > 0 ? 'text-green-600' : 'text-red-500'}">
                        ${actualStock}
                    </td>
                    <td class="px-6 py-4">
                        ${p.image_url ? `<img src="${p.image_url}" class="w-12 h-12 object-cover rounded shadow-sm">` : '<span class="text-xs text-gray-400">Trống</span>'}
                    </td>
                </tr>
            `;
        }
        tbody.innerHTML = html;
        addLog("[HỆ THỐNG] Đã làm mới dữ liệu Bảng điều khiển.");
    } catch (error) {
        console.error('Lỗi tải sản phẩm:', error);
        addLog("Lỗi đồng bộ dữ liệu giữa các Service.", true);
    }
}

// FORM 1: THÊM SẢN PHẨM
const productForm = document.getElementById('product-form');
if (productForm) {
    productForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const token = localStorage.getItem('token');
        const prodId = document.getElementById('product_id').value;
        const formData = new FormData();
        formData.append('id', prodId);
        formData.append('name', document.getElementById('product_name').value);
        formData.append('price', document.getElementById('product_price').value);
        
        const imageFile = document.getElementById('product_image').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        try {
            const response = await fetch('http://localhost:8000/api/products/', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                addLog(`[APP] Khai báo thành công sản phẩm mới: ${prodId}`);
                loadProducts(); 
                productForm.reset();
                document.getElementById('import_product_id').value = prodId;
                document.getElementById('image-preview-el').classList.add('hidden');
                document.getElementById('preview-placeholder').classList.remove('hidden');
            } else {
                addLog(`[LỖI APP] ${data.detail || 'Không thể tạo sản phẩm'}`, true);
            }
        } catch (error) {
            addLog("CRITICAL: Lỗi kết nối tới App Service (Port 8000)", true);
        }
    });
}

// FORM 2: NHẬP KHO
const importForm = document.getElementById('import-form');
if (importForm) {
    importForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const token = localStorage.getItem('token');
        const productId = document.getElementById('import_product_id').value;
        const quantity = document.getElementById('import_quantity').value;

        try {
            const response = await fetch('http://localhost:8001/api/inventory/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ product_id: productId, quantity: parseInt(quantity) })
            });

            const data = await response.json();
            if (response.ok) {
                addLog(`[KHO] Nhập thêm ${quantity} đơn vị cho mã ${productId} thành công.`);
                importForm.reset();
                setTimeout(() => { loadProducts(); }, 1000); 
            } else {
                addLog(`[LỖI KHO] Không thể nhập hàng cho mã ${productId}`, true);
            }
        } catch (error) {
            addLog("CRITICAL: Lỗi kết nối tới Inventory Service (Port 8001)", true);
        }
    });
}

// ==========================================
// THÊM MỚI: QUẢN LÝ ĐƠN HÀNG
// ==========================================
async function loadOrders() {
    const tbody = document.getElementById('order-list');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400 italic">Đang tải đơn hàng...</td></tr>';

    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://localhost:8000/api/orders/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error("Không thể tải danh sách");
        const orders = await response.json();

        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-400">Chưa có đơn hàng nào trong hệ thống.</td></tr>';
            return;
        }

        let html = '';
        // Phối màu cho từng trạng thái giúp Admin nhìn rõ ràng hơn
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
        const response = await fetch(`http://localhost:8000/api/orders/${orderId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
            addLog(`[ĐƠN HÀNG] Đã cập nhật đơn ${orderId} thành ${newStatus}`);
            // Tải lại bảng để nó đổi màu tự động
            loadOrders(); 
        } else {
            const data = await response.json();
            addLog(`[LỖI CẬP NHẬT] ${data.detail}`, true);
            loadOrders(); // Reset lại bảng nếu lỗi
        }
    } catch (error) {
        console.error('Lỗi cập nhật trạng thái:', error);
        addLog("Lỗi kết nối khi cập nhật đơn hàng.", true);
    }
}