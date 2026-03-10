(function checkAuth() {
    const user = localStorage.getItem('ketib_user');
    if (!user) {
        alert("Vui lòng đăng nhập để tiếp tục!");
        window.location.href = "login.html";
    }
})();

const userData = JSON.parse(localStorage.getItem('ketib_user'));
if (userData) {
    document.getElementById('user-display').innerText = `Xin chào, ${userData.full_name}`;
}

// Tìm hàm xử lý nút Checkout trong file app.js của bạn
document.getElementById('checkout-btn').addEventListener('click', async () => {
    // 1. Lấy dữ liệu người dùng từ localStorage
    const userData = JSON.parse(localStorage.getItem('ketib_user'));

    if (!userData || !userData.id) {
        alert("Vui lòng đăng nhập để thực hiện đặt hàng!");
        window.location.href = "login.html";
        return;
    }

    const orderData = {
        user_id: userData.id, // Sử dụng ID thực tế của người dùng
        items: cart.map(item => ({
            product_id: item.id,
            quantity: item.quantity
        }))
    };

    try {
        const response = await fetch("http://localhost:8000/api/orders/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(orderData)
        });

        if (response.ok) {
            alert("Đặt hàng thành công!");
            cart = []; // Xóa giỏ hàng
            updateCartUI();
        } else {
            const err = await response.json();
            alert("Lỗi: " + err.detail);
        }
    } catch (error) {
        alert("Không thể kết nối tới máy chủ.");
    }
});