const API_AUTH = "http://localhost:8000/api/auth";

document.addEventListener('DOMContentLoaded', () => {
    // --- XỬ LÝ ĐĂNG KÝ (REGISTER) ---
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const fullName = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            const confirmPassword = document.getElementById('reg-confirm').value;
            const termsChecked = document.getElementById('terms').checked;

            // 1. Kiểm tra điều khoản
            if (!termsChecked) {
                alert("Bạn phải đồng ý với Điều khoản dịch vụ.");
                return;
            }

            // 2. Kiểm tra khớp mật khẩu
            if (password !== confirmPassword) {
                alert("Mật khẩu xác nhận không khớp. Vui lòng kiểm tra lại.");
                return;
            }

            const userData = {
                full_name: fullName,
                email: email,
                password: password
            };

            try {
                const response = await fetch(`${API_AUTH}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert("Đăng ký thành công! Đang chuyển hướng tới trang đăng nhập...");
                    window.location.href = "login.html";
                } else {
                    alert("Lỗi đăng ký: " + (result.detail || "Vui lòng thử lại"));
                }
            } catch (error) {
                console.error("Lỗi kết nối:", error);
                alert("Không thể kết nối tới máy chủ.");
            }
        });
    }

    // --- XỬ LÝ ĐĂNG NHẬP (LOGIN) ---
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const loginData = {
                email: email,
                password: password
            };

            try {
                const response = await fetch(`${API_AUTH}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(loginData)
                });

                const result = await response.json();

                if (response.ok) {
                    // Lưu thông tin người dùng vào localStorage để sử dụng cho trang app.html
                    localStorage.setItem('ketib_user', JSON.stringify(result.user));
                    
                    alert("Đăng nhập thành công!");
                    window.location.href = "app.html"; // Chuyển hướng tới trang mua sắm
                } else {
                    alert("Đăng nhập thất bại: " + (result.detail || "Sai email hoặc mật khẩu"));
                }
            } catch (error) {
                console.error("Lỗi kết nối:", error);
                alert("Lỗi kết nối hệ thống.");
            }
        });
    }
});

// Hàm hỗ trợ ẩn hiện mật khẩu (nếu bạn dùng nút visibility trong HTML)
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
    } else {
        input.type = "password";
    }
}


