const API_INVENTORY = "http://localhost:8001/api/inventory";

// 1. Lấy dữ liệu tồn kho thực tế
async function loadInventory() {
    try {
        // Giả sử Backend có API lấy toàn bộ, nếu không bạn có thể lấy từng SP theo ID
        const response = await fetch(`${API_INVENTORY}/status/SP01`); // Ví dụ cho SP01
        const data = await response.json();
        
        const list = document.getElementById('inventory-list');
        list.innerHTML = `
            <tr>
                <td class="px-6 py-4 font-bold text-primary">${data.product_id}</td>
                <td class="px-6 py-4 text-center font-mono text-lg">${data.actual_stock}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 ${data.actual_stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} rounded-full text-[10px] uppercase font-bold">
                        ${data.actual_stock > 0 ? 'In Warehouse' : 'Out of Stock'}
                    </span>
                </td>
            </tr>
        `;
        document.getElementById('total-items').innerText = "1 Active SKU";
    } catch (err) {
        console.error("Lỗi load kho:", err);
    }
}

// 2. Xử lý nhập kho (Restock)
document.getElementById('restock-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const productId = document.getElementById('prod-id').value;
    const quantity = parseInt(document.getElementById('prod-qty').value);

    const payload = {
        product_id: productId,
        quantity: quantity
    };

    try {
        const response = await fetch(`${API_INVENTORY}/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            addLog(`SUCCESS: Added ${quantity} units to ${productId}`);
            loadInventory();
            document.getElementById('restock-form').reset();
        } else {
            addLog(`ERROR: Could not restock ${productId}`, true);
        }
    } catch (err) {
        addLog("CRITICAL: Inventory Server Offline", true);
    }
});

// 3. Hàm tạo log giả lập activity
function addLog(message, isError = false) {
    const logContainer = document.getElementById('activity-log');
    const time = new Date().toLocaleTimeString();
    const logItem = document.createElement('div');
    logItem.className = `p-2 rounded border-l-4 ${isError ? 'bg-red-50 border-red-500 text-red-700' : 'bg-green-50 border-green-500 text-green-700'}`;
    logItem.innerHTML = `<strong>[${time}]</strong> ${message}`;
    logContainer.prepend(logItem);
}

// Khởi tạo
document.addEventListener('DOMContentLoaded', loadInventory);