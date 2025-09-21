$(document).ready(function () {
    const apiBase = "/disaster";

    // ----------------------
    // Current User Info
    // ----------------------
    const currentUser = JSON.parse(sessionStorage.getItem('user') || '{}');
    const currentUserId = String(currentUser.id || '');
    const currentUserRole = (currentUser.role || 'user').toLowerCase();

    let editId = null; // Track editing disaster
    const disasterModal = new bootstrap.Modal(document.getElementById("disasterModal"));

    // ----------------------
    // Load Disasters
    // ----------------------
    let disasterTable = null;

function loadDisasters() {
    $.ajax({
        url: `${apiBase}/disaster`,
        method: "GET",
        success: function (data) {
            const tbody = $("#disasterTable tbody");
            tbody.empty();

            data.forEach(d => {
                const ownerId = String(d.reported_by || '');
                const canModify = (currentUserId === ownerId) || ['admin', 'super_admin', 'camp_manager'].includes(currentUserRole);

                tbody.append(`
                    <tr data-id="${d.id}" data-owner-id="${ownerId}">
                        <td>${d.id}</td>
                        <td>${d.name}</td>
                        <td>${d.type}</td>
                        <td>${d.location}</td>
                        <td>${d.severity || "-"}</td>
                        <td>${d.affected_population || "-"}</td>
                        <td>${d.description || "-"}</td>
                        <td>${d.reported_by_name || "-"}</td>
                        <td>
                            <button class="btn btn-sm btn-warning editBtn" ${canModify ? "" : "disabled"}>Edit</button>
                            <button class="btn btn-sm btn-danger deleteBtn" ${canModify ? "" : "disabled"}>Delete</button>
                        </td>
                    </tr>
                `);
            });

            // Destroy old DataTable if exists
            if ($.fn.DataTable.isDataTable('#disasterTable')) {
                $("#disasterTable").DataTable().destroy();
            }

            // Initialize DataTable
            disasterTable = $("#disasterTable").DataTable({
                pageLength: 5,
                lengthMenu: [5, 10, 25, 50],
                columnDefs: [{ orderable: false, targets: 8 }], // disable sorting on actions
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                }
            });
        },
        error: function () {
            Swal.fire("Error", "Failed to load disasters", "error");
        }
    });
}

    loadDisasters();

    // ----------------------
    // Add Disaster Modal
    // ----------------------
    $("#addDisasterBtn").click(function () {
        editId = null;
        $("#disasterForm")[0].reset();
        $("#disasterModalLabel").text("Add Disaster");
        disasterModal.show();
    });

    // ----------------------
    // Submit Add/Edit Disaster
    // ----------------------
    $("#disasterForm").submit(function (e) {
        e.preventDefault();

        const formData = Object.fromEntries($(this).serializeArray().map(i => [i.name, i.value]));
        const method = editId ? "PUT" : "POST";
        const url = editId ? `${apiBase}/${editId}` : `${apiBase}/create`;

        $.ajax({
            url: url,
            method: method,
            contentType: "application/json",
            headers: { "X-Role": currentUserRole }, // send lowercase role
            data: JSON.stringify(formData),
            success: function (res) {
                Swal.fire("Success", res.message, "success");
                disasterModal.hide();
                loadDisasters();
            },
            error: function (xhr) {
                Swal.fire("Error", xhr.responseJSON?.error || "Operation failed", "error");
            }
        });
    });

    // ----------------------
    // Edit Disaster
    // ----------------------
    $("#disasterTable").on("click", ".editBtn", function () {
        const tr = $(this).closest("tr");
        const ownerId = String(tr.data("owner-id"));
        const canEdit = (currentUserId === ownerId) || ['admin', 'super_admin', 'camp_manager'].includes(currentUserRole);

        if (!canEdit) {
            Swal.fire("Unauthorized", "You cannot edit this disaster.", "error");
            return;
        }

        editId = tr.data("id");

        // Fill form with current data
        $("#disasterForm [name=name]").val(tr.find("td:eq(1)").text());
        $("#disasterForm [name=type]").val(tr.find("td:eq(2)").text());
        $("#disasterForm [name=location]").val(tr.find("td:eq(3)").text());
        $("#disasterForm [name=severity]").val(tr.find("td:eq(4)").text() === "-" ? "" : tr.find("td:eq(4)").text());
        $("#disasterForm [name=affected_population]").val(tr.find("td:eq(5)").text() === "-" ? "" : tr.find("td:eq(5)").text());
        $("#disasterForm [name=description]").val(tr.find("td:eq(6)").text() === "-" ? "" : tr.find("td:eq(6)").text());

        $("#disasterModalLabel").text("Edit Disaster");
        disasterModal.show();
    });

    // ----------------------
    // Delete Disaster
    // ----------------------
    $("#disasterTable").on("click", ".deleteBtn", function () {
        const tr = $(this).closest("tr");
        const ownerId = String(tr.data("owner-id"));
        const canDelete = (currentUserId === ownerId) || ['admin', 'super_admin', 'camp_manager'].includes(currentUserRole);

        if (!canDelete) {
            Swal.fire("Unauthorized", "You cannot delete this disaster.", "error");
            return;
        }

        const id = tr.data("id");

        Swal.fire({
            title: "Are you sure?",
            text: "This will delete the disaster!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, delete it!"
        }).then(result => {
            if (result.isConfirmed) {
                $.ajax({
                    url: `${apiBase}/${id}`,
                    method: "DELETE",
                    headers: { "X-Role": currentUserRole }, // lowercase role
                    success: function (res) {
                        Swal.fire("Deleted!", res.message, "success");
                        loadDisasters();
                    },
                    error: function (xhr) {
                        Swal.fire("Error", xhr.responseJSON?.error || "Failed to delete", "error");
                    }
                });
            }
        });
    });
});
