document.addEventListener("DOMContentLoaded", () => {
    const apiBase = "/message";
    const userApi = "/user/users";
    let currentUser = null;
    let activeChatUser = null;

    // Track last message ID per sender to prevent duplicate toasts
    const lastMessageIds = {};

    const conversationList = document.getElementById("conversationList");
    const chatMessages = document.getElementById("chatMessages");
    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendMessage");

    // ---------------------------- Load current user ----------------------------
    // ---------------------------- Load current user ----------------------------
    // ---------------------------- Load current user ----------------------------
    async function loadCurrentUser() {
        try {
            const res = await fetch("/auth/current");
            const data = await res.json();

            if (!data.user) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Not Logged In',
                    text: 'Please log in to access messages.',
                    confirmButtonText: 'Go to Login'
                }).then(() => {
                    window.location.href = "/login"; // redirect to login page
                });
                return;
            }

            currentUser = data.user;
            if (conversationList) loadConversations();
            startMessagePolling();
        } catch {
            console.error("Please log in first");
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'You are not logged in. Please log in to access messages.',
                confirmButtonText: 'Go to Login'
            }).then(() => {
                window.location.href = "/login";
            });
        }
    }



    // ---------------------------- Load conversation list ----------------------------
    async function loadConversations() {
        try {
            const res = await fetch(userApi);
            const users = await res.json();
            conversationList.innerHTML = "";

            users.forEach(u => {
                if (u.id !== parseInt(currentUser.id)) {
                    const a = document.createElement("a");
                    a.href = "#";
                    a.className = "list-group-item list-group-item-action conversation-item";
                    a.dataset.id = u.id;
                    a.dataset.name = u.name;
                    a.innerHTML = `<i class="bi bi-person-circle me-2"></i> ${u.name}`;
                    conversationList.appendChild(a);
                }
            });
        } catch {
            console.error("Failed to load users");
        }
    }

    // ---------------------------- Load conversation messages ----------------------------
    async function loadConversation(otherUserId, otherUserName) {
        activeChatUser = { id: otherUserId, name: otherUserName };
        document.getElementById("chatWith").textContent = `Chat with ${otherUserName}`;

        try {
            const res = await fetch(`${apiBase}/conversation/${currentUser.id}/${otherUserId}`);
            const messages = await res.json();
            chatMessages.innerHTML = "";

            if (!messages.length) {
                chatMessages.innerHTML = `<p class="text-muted text-center">No messages yet</p>`;
            }

            messages.forEach(renderMessage);
            lastMessageIds[otherUserId] = messages.length ? messages[messages.length - 1].id : 0;

            scrollToBottom();

            // Mark conversation as read on server
            await fetch(`${apiBase}/mark_read/${otherUserId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_user_id: currentUser.id })
            });
        } catch {
            console.error("Failed to load messages");
        }
    }

    // ---------------------------- Render a single message ----------------------------
    function renderMessage(m) {
        const type = m.sender_id === parseInt(currentUser.id) ? "sent" : "received";
        const div = document.createElement("div");
        div.className = `chat-message ${type}`;
        div.innerHTML = `
            <div class="bubble">${escapeHtml(m.content)}</div>
            <div><small class="text-muted">${formatTime(m.sent_at)}</small></div>
        `;
        chatMessages.appendChild(div);
    }

    function escapeHtml(text) {
        return document.createElement("div").appendChild(document.createTextNode(text)).parentNode.innerHTML;
    }

    function formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ---------------------------- Send message ----------------------------
    async function sendMessage() {
        if (!activeChatUser) return;
        const text = messageInput.value.trim();
        if (!text) return;

        try {
            const res = await fetch(`${apiBase}/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    sender_id: currentUser.id,
                    receiver_id: activeChatUser.id,
                    content: text
                })
            });
            const data = await res.json();
            renderMessage(data.data);
            lastMessageIds[activeChatUser.id] = data.data.id;
            messageInput.value = "";
            scrollToBottom();
        } catch {
            console.error("Failed to send message");
        }
    }

    sendBtn?.addEventListener("click", sendMessage);
    messageInput?.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // ---------------------------- Click on conversation ----------------------------
    conversationList?.addEventListener("click", (e) => {
        const target = e.target.closest(".conversation-item");
        if (!target) return;
        e.preventDefault();
        loadConversation(target.dataset.id, target.dataset.name);
    });

    // ---------------------------- Polling for new messages ----------------------------
    function startMessagePolling() {
        async function poll() {
            try {
                const res = await fetch(`${apiBase}/latest/${currentUser.id}`);
                const messages = await res.json();

                messages.forEach(msg => {
                    const senderId = msg.sender_id;
                    const lastId = lastMessageIds[senderId] || 0;

                    if (msg.id > lastId) {
                        lastMessageIds[senderId] = msg.id;

                        if (activeChatUser && senderId === parseInt(activeChatUser.id)) {
                            // If actively viewing conversation, append directly
                            renderMessage(msg);
                            scrollToBottom();

                            // Mark messages as read on server
                            fetch(`${apiBase}/mark_read/${senderId}`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ current_user_id: currentUser.id })
                            });
                        } else {
                            showToast(msg.sender_name, msg.content);
                        }
                    }
                });
            } catch (err) {
                console.error("Polling error:", err);
            } finally {
                setTimeout(poll, 120000); // poll every 5s
            }
        }
        poll();
    }

    // ---------------------------- Show toast ----------------------------
    function showToast(senderName, text) {
        const toastContainer = document.getElementById("toastContainer");
        if (!toastContainer) return;

        const toastDiv = document.createElement("div");
        toastDiv.className = "toast align-items-center text-bg-primary border-0 shadow-lg mb-2";
        toastDiv.setAttribute("role", "alert");
        toastDiv.setAttribute("aria-live", "assertive");
        toastDiv.setAttribute("aria-atomic", "true");
        toastDiv.innerHTML = `
            <div class="d-flex">
                <div class="toast-body"><strong>${escapeHtml(senderName)}</strong>: ${escapeHtml(text)}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toastDiv);
        const toast = new bootstrap.Toast(toastDiv, { delay: 5000 });
        toast.show();

        toastDiv.addEventListener("click", () => window.location.href = "/message");
        toastDiv.addEventListener("hidden.bs.toast", () => toastDiv.remove());
    }

    loadCurrentUser();
});
