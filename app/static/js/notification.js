document.addEventListener("DOMContentLoaded", () => {
    const notificationList = document.getElementById("notificationList");
    const unreadCountElem = document.getElementById("unreadCount");
    const adminSendDiv = document.getElementById("adminSend");
    const sendBtn = document.getElementById("sendNotificationBtn");
    const toastEl = document.getElementById('notificationToast');
    const toastBody = toastEl?.querySelector('.toast-body');
    const toast = toastEl ? new bootstrap.Toast(toastEl) : null;

    const role = document.body.dataset.role;

    if (["admin", "super_admin"].includes(role)) {
        adminSendDiv.classList.remove("d-none");
    }

    let lastUnreadIds = new Set();

    async function fetchNotifications(showToast = true) {
        try {
            const res = await fetch("/notification/api");
            if (!res.ok) return;
            const data = await res.json();

            if (notificationList) notificationList.innerHTML = "";
            let unreadCount = 0;
            let hasNewUnread = false;

            data.forEach(n => {
                if (notificationList) {
                    const li = document.createElement("li");
                    li.className = `list-group-item ${n.is_read ? "read" : "unread"}`;
                    li.dataset.id = n.id;
                    li.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <span>${n.message}</span>
                            <small class="text-muted">${new Date(n.created_at).toLocaleString()}</small>
                        </div>
                        <button class="btn btn-sm btn-success mt-1 mark-read-btn" ${n.is_read ? "disabled" : ""}>
                            Mark as Read
                        </button>
                    `;
                    notificationList.appendChild(li);
                }

                if (!n.is_read) {
                    unreadCount++;
                    if (!lastUnreadIds.has(n.id)) {
                        lastUnreadIds.add(n.id);
                        hasNewUnread = true;
                    }
                }
            });

            if (unreadCountElem) unreadCountElem.textContent = unreadCount;

            if (showToast && hasNewUnread && toast) {
                toast.show();
            }
        } catch (err) {
            console.error("Failed to fetch notifications:", err);
        }
    }

    // Redirect toast click to notification page if list doesn't exist
    toastBody?.addEventListener("click", () => {
        if (notificationList) {
            notificationList.scrollIntoView({ behavior: "smooth", block: "start" });
        } else {
            window.location.href = "/notification";
        }
        toast.hide();
    });

    if (notificationList) {
        notificationList.addEventListener("click", async (e) => {
            if (!e.target.classList.contains("mark-read-btn")) return;
            const li = e.target.closest("li");
            const id = li.dataset.id;
            try {
                const res = await fetch(`/notification/${id}/read`, { method: "PUT" });
                if (res.ok) {
                    li.classList.replace("unread", "read");
                    e.target.disabled = true;
                    unreadCountElem.textContent = Math.max(0, unreadCountElem.textContent - 1);
                    lastUnreadIds.delete(parseInt(id));
                }
            } catch (err) {
                console.error("Failed to mark notification as read:", err);
            }
        });
    }

    sendBtn?.addEventListener("click", async () => {
        const userId = document.getElementById("targetUserId").value.trim();
        const message = document.getElementById("notificationMessage").value.trim();
        if (!userId || !message) {
            Swal.fire('Warning', 'Please enter User ID and message', 'warning');
            return;
        }

        try {
            const res = await fetch("/notification/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, message })
            });
            const data = await res.json();

            if (res.ok) {
                Swal.fire('Success', 'Notification sent!', 'success');
                document.getElementById("targetUserId").value = "";
                document.getElementById("notificationMessage").value = "";
                fetchNotifications(false);
            } else {
                Swal.fire('Error', data.error || 'Failed to send notification', 'error');
            }
        } catch (err) {
            console.error("Failed to send notification:", err);
            Swal.fire('Error', 'Failed to send notification', 'error');
        }
    });

    fetchNotifications(true);
    setInterval(() => fetchNotifications(true), 30000);
});
