$(document).ready(function () {
    let table = $('#reliefRequestTable').DataTable();
    let currentUser = null;

    init();

    async function init() {
        currentUser = await getCurrentUser();
        if (!currentUser) {
            Swal.fire("Unauthorized", "Please login first", "warning");
            return;
        }
        loadReliefRequests();
    }

    // ---------------- Helpers ----------------
    async function getCurrentUser() {
        try {
            const res = await fetch("/auth/current");
            if (!res.ok) throw new Error("Failed to fetch current user");
            const data = await res.json();
            return data.user;
        } catch (err) {
            console.error(err);
            return null;
        }
    }

    async function loadReliefRequests() {
        try {
            const res = await fetch("/reliefRequest/api");
            if (!res.ok) throw new Error("Failed to fetch requests");
            const requests = await res.json();

            table.clear();
            requests.forEach(r => {
                const isOwner = currentUser && r.user_id === parseInt(currentUser.id);
                const isAdmin = currentUser && ["admin", "super_admin"].includes(currentUser.role);

                let actionBtns = "";
                if (isOwner || isAdmin) {
                    actionBtns = `
                        <button class="btn btn-sm btn-primary editBtn" data-id="${r.id}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger deleteBtn" data-id="${r.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    `;
                }

                table.row.add([
                    r.id,
                    r.disaster_id,
                    r.resource_needed,
                    r.quantity,
                    r.status,
                    actionBtns
                ]);
            });
            table.draw();
        } catch (err) {
            console.error(err);
            Swal.fire("Error", "Could not load relief requests", "error");
        }
    }

    // ---------------- Create/Edit ----------------
    $("#reliefRequestForm").on("submit", async function (e) {
        e.preventDefault();

        const id = $("#request_id").val();
        const disaster_id = $("#disaster_id").val();
        const resource_needed = $("#resource_needed").val();
        const quantity = $("#quantity").val();
        let status = $("#status").val();

        // Normal users → force status to "Pending" on creation
        if (!["admin", "super_admin"].includes(currentUser.role)) {
            status = "Pending";
        }

        const requestData = { disaster_id, resource_needed, quantity, status };

        try {
            let url = "/reliefRequest/create";
            let method = "POST";

            if (id) {
                // Edit mode
                url = `/reliefRequest/${id}`;
                method = "PUT";
            }

            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData)
            });

            if (!res.ok) throw new Error("Request failed");

            $("#reliefRequestModal").modal("hide");
            Swal.fire("Success", "Relief request saved successfully!", "success");
            loadReliefRequests();
        } catch (err) {
            Swal.fire("Error", "Failed to save request", "error");
        }
    });


    // ---------------- Edit ----------------
    $('#reliefRequestTable').on("click", ".editBtn", async function () {
        const id = $(this).data("id");
        try {
            const res = await fetch(`/reliefRequest/${id}`);
            if (!res.ok) throw new Error("Failed to fetch request");
            const r = await res.json();

            // Fill form fields
            $("#request_id").val(r.id);
            $("#disaster_id").val(r.disaster_id);
            $("#resource_needed").val(r.resource_needed);
            $("#quantity").val(r.quantity);

            // -------- Role-based status control --------
            const statusSelect = $("#status");
            statusSelect.empty(); // clear previous options

            if (currentUser && ["admin", "super_admin"].includes(currentUser.role)) {
                // Admins: full status options
                ["Pending", "Approved", "Fulfilled"].forEach(s => {
                    const selected = r.status === s ? "selected" : "";
                    statusSelect.append(`<option value="${s}" ${selected}>${s}</option>`);
                });
                statusSelect.prop("disabled", false);
            } else {
                // Normal users: only show current status (usually Pending)
                statusSelect.append(`<option value="${r.status}" selected>${r.status}</option>`);
                statusSelect.prop("disabled", true);
            }

            $("#reliefRequestModal").modal("show");

        } catch (err) {
            Swal.fire("Error", "Failed to load request details", "error");
        }
    });

    // ---------------- Delete ----------------
    $('#reliefRequestTable').on("click", ".deleteBtn", function () {
        const id = $(this).data("id");

        Swal.fire({
            title: "Are you sure?",
            text: "This request will be permanently deleted.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, delete it!"
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/reliefRequest/${id}`, { method: "DELETE" });
                    if (!res.ok) throw new Error("Delete failed");
                    Swal.fire("Deleted!", "Relief request has been deleted.", "success");
                    loadReliefRequests();
                } catch (err) {
                    Swal.fire("Error", "Could not delete request", "error");
                }
            }
        });
    });
});
