const API_APP = "http://localhost:8000/api";
const API_INVENTORY = "http://localhost:8001/api/inventory";

/**
 * 1. Logic chuyển đổi giao diện (Tabs)
 */
function switchSection(sectionName) {
    // Ẩn tất cả các section và hiện section được chọn
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`section-${sectionName}`).classList.add('active');

    // Cập nhật trạng thái menu bên trái
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.getElementById(`nav-${sectionName}`).classList.add('active');

    // Cập nhật tiêu đề Header
    const title = sectionName.charAt(0).toUpperCase() + sectionName.slice(1);
    document.getElementById('header-title').innerText = `${title} Overview`;

    // Tự động tải danh sách nếu chuyển sang tab Inventory
    if (sectionName === 'inventory') {
        loadInventoryList();
    }
}

/**
 * 2. Logic nghiệp vụ Dashboard (Tạo SP & Nhập kho)
 */

// Form tạo sản phẩm mới (Hỗ trợ Upload Ảnh qua FormData)
document.getElementById('create-product-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Sử dụng FormData để có thể gửi tệp tin (binary)
    const formData = new FormData();
    formData.append('id', document.getElementById('new-prod-id').value);
    formData.append('name', document.getElementById('new-prod-name').value);
    formData.append('price', document.getElementById('new-prod-price').value);
    
    const imageFile = document.getElementById('new-prod-image').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    try {
        const response = await fetch(`${API_APP}/products/`, {
            method: 'POST',
            // Lưu ý: Không đặt Content-Type khi gửi FormData, trình duyệt sẽ tự xử lý
            body: formData
        });

        if (response.ok) {
            addLog(`[APP] Khai báo thành công sản phẩm: ${document.getElementById('new-prod-id').value}`);
            e.target.reset();
            // Reset ảnh xem trước
            document.getElementById('image-preview-el').classList.add('hidden');
            document.getElementById('preview-placeholder').classList.remove('hidden');
            // Gợi ý ID sang form nhập kho
            document.getElementById('prod-id').value = formData.get('id');
        } else {
            const err = await response.json();
            addLog(`[LỖI APP] ${err.detail || 'Không thể tạo sản phẩm'}`, true);
        }
    } catch (err) {
        addLog("CRITICAL: Lỗi kết nối tới App Service (Port 8000)", true);
    }
});

// Form nhập kho (Inventory Service)
document.getElementById('restock-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const productId = document.getElementById('prod-id').value;
    const quantity = parseInt(document.getElementById('prod-qty').value);

    try {
        const response = await fetch(`${API_INVENTORY}/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: quantity })
        });

        if (response.ok) {
            addLog(`[KHO] Nhập thêm ${quantity} đơn vị cho mã ${productId} thành công.`);
            e.target.reset();
        } else {
            addLog(`[LỖI KHO] Không thể nhập hàng cho mã ${productId}`, true);
        }
    } catch (err) {
        addLog("CRITICAL: Lỗi kết nối tới Inventory Service (Port 8001)", true);
    }
});

/**
 * 3. Logic nghiệp vụ Inventory (Xem danh sách)
 */
async function loadInventoryList() {
    const tableBody = document.getElementById('inventory-list-table');
    tableBody.innerHTML = '<tr><td colspan="4" class="p-6 text-center text-gray-400 italic">Đang tải dữ liệu từ hệ thống...</td></tr>';

    try {
        // Lấy danh mục sản phẩm từ App Service
        const resApp = await fetch(`${API_APP}/products/`);
        const products = await resApp.json();

        if (products.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" class="p-6 text-center text-gray-400">Hệ thống chưa có sản phẩm nào.</td></tr>';
            return;
        }

        let html = '';
        for (const p of products) {
            let stock = 0;
            try {
                // Lấy tồn kho thực tế từ Inventory Service
                const resInv = await fetch(`${API_INVENTORY}/status/${p.id}`);
                const invData = await resInv.json();
                stock = invData.stock ?? 0;
            } catch (e) { console.error(`Không lấy được stock cho ${p.id}`); }

            html += `
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-6 py-4 font-bold text-primary">${p.id}</td>
                    <td class="px-6 py-4">${p.name}</td>
                    <td class="px-6 py-4 text-center font-mono font-bold text-lg">${stock}</td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 ${stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} rounded-full text-[10px] uppercase font-bold">
                            ${stock > 0 ? 'In Warehouse' : 'Out of Stock'}
                        </span>
                    </td>
                </tr>
            `;
        }
        tableBody.innerHTML = html;
    } catch (err) {
        tableBody.innerHTML = '<tr><td colspan="4" class="p-6 text-center text-red-500 font-bold">Lỗi đồng bộ dữ liệu giữa các Service.</td></tr>';
    }
}

/**
 * 4. Tiện ích Log
 */
function addLog(message, isError = false) {
    const logContainer = document.getElementById('activity-log');
    const logItem = document.createElement('div');
    const time = new Date().toLocaleTimeString();
    
    logItem.className = isError ? 'text-red-500 font-semibold' : 'text-green-600';
    logItem.innerHTML = `<span class="text-gray-400">[${time}]</span> ${message}`;
    
    logContainer.prepend(logItem);
}

// Khởi tạo trạng thái ban đầu
document.addEventListener('DOMContentLoaded', () => {
    switchSection('dashboard');
});