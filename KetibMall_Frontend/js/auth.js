// ==========================================
// 1. XỬ LÝ ĐĂNG NHẬP
// ==========================================
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                alert('Đăng nhập thành công!');
                
                // Lưu Token và thông tin User vào trình duyệt
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));

                // Điều hướng dựa theo quyền (Role)
                if (data.user.role === 'admin') {
                    window.location.href = 'admin.html';
                } else {
                    window.location.href = 'app.html';
                }
            } else {
                alert(data.detail || 'Đăng nhập thất bại! Vui lòng kiểm tra lại thông tin.');
            }
        } catch (error) {
            console.error('Lỗi đăng nhập:', error);
            alert('Lỗi kết nối đến máy chủ.');
        }
    });
}

// ==========================================
// 2. XỬ LÝ ĐĂNG KÝ
// ==========================================
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fullName = document.getElementById('full_name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('http://localhost:8000/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    full_name: fullName, 
                    email: email, 
                    password: password,
                    role: 'customer' // Mặc định đăng ký là khách hàng
                })
            });

            const data = await response.json();
            if (response.ok) {
                alert('Đăng ký thành công! Vui lòng đăng nhập.');
                window.location.href = 'login.html';
            } else {
                alert(data.detail || 'Đăng ký thất bại!');
            }
        } catch (error) {
            console.error('Lỗi đăng ký:', error);
            alert('Lỗi kết nối đến máy chủ.');
        }
    });
}

// ==========================================
// 3. CHỨC NĂNG ĐĂNG XUẤT
// ==========================================
function logout() {
    // Xóa Token và dữ liệu User
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

// Tự động gắn sự kiện nếu trên trang có nút mang id="logout-btn"
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
});