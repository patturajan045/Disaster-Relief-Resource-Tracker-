$(document).ready(function () {
    // ----------------------
    // Helper Functions
    // ----------------------
    function saveUserSession(user) {
        const normalizedUser = {
            id: user.id,
            name: user.name,
            email: user.email,
            role: user.role.toLowerCase()
        };
        sessionStorage.setItem('user', JSON.stringify(normalizedUser));

        // Optional: update <body> attributes if pages rely on them
        document.body.dataset.userId = normalizedUser.id;
        document.body.dataset.userRole = normalizedUser.role;
    }

    function getCurrentUser() {
        return JSON.parse(sessionStorage.getItem('user') || '{}');
    }

    function isAdminOrSuper() {
        const user = getCurrentUser();
        return ['admin', 'super_admin'].includes(user.role);
    }

    // ----------------------
    // Login Form
    // ----------------------
    $('#loginForm').submit(function (e) {
        e.preventDefault();
        const formData = Object.fromEntries($(this).serializeArray().map(i => [i.name, i.value]));
        formData.action = 'login';

        $.ajax({
            url: '/auth/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function (res) {
                Swal.fire('Success', res.message, 'success');

                saveUserSession({
                    id: res.id || res.user_id,
                    name: res.name || '',
                    email: res.email,
                    role: res.role
                });

                // Redirect to dashboard
                window.location.href = '/index';
            },
            error: function (xhr) {
                Swal.fire('Error', xhr.responseJSON?.error || 'Login failed', 'error');
            }
        });
    });

    // ----------------------
    // Register Form
    // ----------------------
    $('#registerForm').submit(function (e) {
        e.preventDefault();

        // Collect form data
        const formData = Object.fromEntries(
            $(this).serializeArray().map(i => [i.name, i.value])
        );
        formData.action = 'register';

        // Password confirmation check
        if (formData.password !== formData.confirmPassword) {
            Swal.fire('Error', 'Passwords do not match', 'error');
            return;
        }

        // AJAX request
        $.ajax({
            url: '/auth/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function (res) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success',
                    text: res.message,
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    // Redirect to login page
                    window.location.href = '/auth/login';
                });
            },
            error: function (xhr) {
                Swal.fire('Error', xhr.responseJSON?.error || 'Registration failed', 'error');
            }
        });
    });


    // ----------------------
    // Logout
    // ----------------------
    $('#logoutBtn').click(function () {
        $.ajax({
            url: '/auth/logout',
            method: 'POST',
            success: function (res) {
                sessionStorage.removeItem('user');
                Swal.fire('Success', res.message, 'success').then(() => {
                    window.location.href = '/login';
                });
            },
            error: function () {
                Swal.fire('Error', 'Logout failed', 'error');
            }
        });
    });

    // ----------------------
    // Promote/Demote Users (Admin Only)
    // ----------------------
    $('#promoteBtn').click(function () {
        if (!isAdminOrSuper()) {
            Swal.fire('Unauthorized', 'Only admin or super admin can promote users', 'error');
            return;
        }

        const targetEmail = $('#targetEmail').val();
        const newRole = $('#newRole').val();
        const currentUser = getCurrentUser();

        $.ajax({
            url: '/auth/promote',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({
                admin_email: currentUser.email,
                email: targetEmail,
                role: newRole
            }),
            success: function (res) {
                Swal.fire('Success', res.message, 'success');
                $('#promoteForm')[0].reset();
            },
            error: function (xhr) {
                Swal.fire('Error', xhr.responseJSON?.error || 'Promotion failed', 'error');
            }
        });
    });

    // ----------------------
    // Disable admin-only UI if not admin
    // ----------------------
    if (!isAdminOrSuper()) {
        $('.adminOnly').prop('disabled', true);
    }
});
