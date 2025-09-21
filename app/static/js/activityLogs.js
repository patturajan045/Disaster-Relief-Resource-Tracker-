// static/js/activityLogs.js
$(document).ready(function () {
    const apiBase = "/auditLog";

    // Initialize DataTable
    const table = $("#auditLogsTable").DataTable({
        ajax: {
            url: `${apiBase}/`,
            dataSrc: "" // API returns array directly
        },
        columns: [
            { data: "id" },
            {
                data: null,
                render: row => `
                    ${row.user_name || "Unknown"}
                    <br><small class="text-muted">ID: ${row.user_id || "N/A"}</small>
                `
            },
            {
                data: "action",
                render: action =>
                    `<span class="badge bg-${getActionColor(action)}">${action}</span>`
            },
            { data: "details", defaultContent: "-" },
            {
                data: "created_at",
                render: date => formatDate(date)
            },
            {
                data: null,
                orderable: false,
                render: row => `
                    <button class="btn btn-sm btn-outline-danger delete-log" data-id="${row.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                `
            }
        ],
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50],
        order: [[4, "desc"]], // Sort by timestamp DESC
        dom: '<"d-flex justify-content-between mb-2"lf>tip',
        responsive: true
    });

    // Map actions to Bootstrap colors
    function getActionColor(action) {
        const map = {
            CREATE: "success",
            UPDATE: "primary",
            DELETE: "danger",
            LOGIN: "warning text-dark"
        };
        return map[action] || "secondary";
    }

    // Convert ISO date → readable format
    function formatDate(isoString) {
        return new Date(isoString).toLocaleString();
    }

    // 🔹 Delete single log with SweetAlert
    $("#auditLogsTable").on("click", ".delete-log", function () {
        const logId = $(this).data("id");

        Swal.fire({
            title: `Delete log #${logId}?`,
            text: "This action cannot be undone.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#6c757d",
            confirmButtonText: "Yes, delete it!"
        }).then(result => {
            if (result.isConfirmed) {
                $.ajax({
                    url: `${apiBase}/${logId}`,
                    type: "DELETE",
                    success: res => {
                        table.ajax.reload(null, false); // reload without resetting page
                        Swal.fire("Deleted!", res.message || "Log deleted successfully.", "success");
                    },
                    error: err => {
                        console.error("Delete failed:", err);
                        Swal.fire("Error!", "Failed to delete the log.", "error");
                    }
                });
            }
        });
    });

    // 🔹 Clear all logs with SweetAlert
    $("#clearAllLogs").on("click", function () {
        Swal.fire({
            title: "Clear All Logs?",
            text: "⚠️ This will permanently remove ALL audit logs!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#6c757d",
            confirmButtonText: "Yes, clear all"
        }).then(result => {
            if (result.isConfirmed) {
                $.ajax({
                    url: `${apiBase}/clear`,
                    type: "DELETE",
                    success: res => {
                        table.ajax.reload();
                        Swal.fire("Cleared!", res.message || "All logs have been deleted.", "success");
                    },
                    error: err => {
                        console.error("Failed to clear logs:", err);
                        Swal.fire("Error!", "Could not clear all logs.", "error");
                    }
                });
            }
        });
    });

    // 🔹 Filter by action (server-side)
    $("#actionFilter").on("change", function () {
        const action = $(this).val();
        table.ajax.url(action ? `${apiBase}/action/${action}` : `${apiBase}/`).load();
    });

    // 🔹 Filter by date (client-side)
    $("#dateFilter").on("change", function () {
        const selectedDate = $(this).val(); // yyyy-mm-dd
        table.column(4).search(selectedDate || "", true, false).draw();
    });
});
