document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // 1. FORM ĐĂNG NHẬP (Dùng định dạng Form URL-Encoded)
    // ==========================================
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // ĐIỂM QUAN TRỌNG: FastAPI OAuth2 yêu cầu dữ liệu gửi dạng Form
            // và tên trường BẮT BUỘC phải là "username" (dù mình truyền email vào)
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            try {
                const response = await fetch('http://localhost:8000/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded' // Khác với lúc đăng ký!
                    },
                    body: formData.toString()
                });

                const data = await response.json();

                if (response.ok) {
                    // Lưu Token và thông tin User vào bộ nhớ trình duyệt
                    localStorage.setItem('token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Phân quyền chuyển hướng
                    if (data.user.role === 'admin') {
                        window.location.href = 'admin.html';
                    } else {
                        window.location.href = 'app.html';
                    }
                } else {
                    // Xử lý triệt để lỗi [object Object]
                    if (Array.isArray(data.detail)) {
                        alert("Lỗi dữ liệu: FastAPI từ chối định dạng này.");
                        console.error("Chi tiết 422:", data.detail);
                    } else {
                        alert(data.detail || 'Sai tài khoản hoặc mật khẩu!');
                    }
                }
            } catch (error) {
                console.error('Lỗi đăng nhập:', error);
                alert('Lỗi kết nối đến máy chủ!');
            }
        });
    }

    // ==========================================
    // 2. FORM ĐĂNG KÝ (Dùng JSON bình thường)
    // ==========================================
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fullName = document.getElementById('full_name').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Đăng ký thì lại dùng JSON theo cấu trúc Pydantic
            const payload = {
                full_name: fullName,
                email: email,
                password: password,
                role: "customer" // Mặc định là khách hàng
            };

            try {
                const response = await fetch('http://localhost:8000/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Đăng ký thành công! Vui lòng đăng nhập.');
                    window.location.href = 'login.html';
                } else {
                    if (Array.isArray(data.detail)) {
                        alert("Lỗi dữ liệu: Vui lòng kiểm tra lại thông tin đăng ký.");
                    } else {
                        alert(data.detail || 'Lỗi đăng ký!');
                    }
                }
            } catch (error) {
                console.error('Lỗi đăng ký:', error);
                alert('Lỗi kết nối máy chủ!');
            }
        });
    }
});

// ==========================================
// 3. LOGIC ĐĂNG XUẤT (Dùng chung)
// ==========================================
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    });
}