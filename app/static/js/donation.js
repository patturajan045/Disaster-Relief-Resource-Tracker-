$(document).ready(function () {
    const donationTable = $('#donationTable').DataTable({
        destroy: true, // ensures old table is removed before reinitializing
        order: [[0, "desc"]]
    });
    let currentUser = null;
    let reloadTimeout = null;

    // ---------------- SweetAlert2 Helpers ----------------
    const showSuccess = msg => Swal.fire({ icon: "success", title: "Success", text: msg, timer: 2000, showConfirmButton: false });
    const showError = msg => Swal.fire({ icon: "error", title: "Error", text: msg });

    // ---------------- Debounced Reload ----------------
    function debouncedReloadResources() {
        if (reloadTimeout) clearTimeout(reloadTimeout);
        reloadTimeout = setTimeout(() => document.dispatchEvent(new Event("donation-changed")), 300);
    }

    // ---------------- Init ----------------
    init();

    async function init() {
        currentUser = await getCurrentUser();
        if (!currentUser) {
            Swal.fire("Unauthorized", "Please login first", "warning");
            return;
        }
        loadDonations();
    }

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

    // ---------------- Load Donations ----------------
    async function loadDonations() {
        try {
            const res = await fetch("/donation/api");
            if (!res.ok) throw new Error("Failed to load donations");
            const donations = await res.json();

            donationTable.clear();
            donations.forEach(d => {
                const isOwner = currentUser && d.donated_by === parseInt(currentUser.id);
                const isAdmin = currentUser && ["admin", "super_admin"].includes(currentUser.role);

                let actionBtns = "";
                if (isOwner || isAdmin) {
                    actionBtns = `
                        <button class="btn btn-sm btn-primary editBtn" data-id="${d.id}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger deleteBtn" data-id="${d.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    `;
                }

                donationTable.row.add([
                    d.id,
                    d.donor_name,
                    d.resource_type || "-",
                    d.quantity || "-",
                    d.unit || "-",
                    d.amount || "-",
                    d.disaster_id || "-",
                    new Date(d.donated_at).toLocaleString(),
                    actionBtns
                ]);
            });
            donationTable.draw();

            // Notify resource script
            debouncedReloadResources();

        } catch (err) {
            console.error(err);
            Swal.fire("Error", "Could not load donations", "error");
        }
    }

    // ---------------- Form Submit ----------------
    $("#donationForm").on("submit", async function (e) {
        e.preventDefault();

        const id = $("#donation_id").val();
        const donationData = {
            donor_name: $("#donor_name").val(),
            resource_type: $("#resource_type").val(),
            quantity: parseInt($("#quantity").val()) || 0,
            unit: $("#unit").val(),
            amount: parseFloat($("#amount").val()) || 0,
            disaster_id: parseInt($("#disaster_id").val()) || null
        };

        try {
            const url = id ? `/donation/${id}` : "/donation/create";
            const method = id ? "PUT" : "POST";

            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(donationData)
            });

            const result = await res.json();
            if (res.ok) {
                $("#donationModal").modal("hide");
                showSuccess(result.message || "Donation saved successfully!");
                $("#donationForm")[0].reset();
                $("#donation_id").val("");

                loadDonations();
                debouncedReloadResources();
            } else {
                showError(result.error || result.message || "Error saving donation");
            }
        } catch (err) {
            console.error(err);
            showError("Server error while saving donation");
        }
    });

    // ---------------- Edit Donation ----------------
    $('#donationTable').on("click", ".editBtn", async function () {
        const id = $(this).data("id");
        try {
            const res = await fetch(`/donation/${id}`);
            if (!res.ok) throw new Error("Failed to fetch donation");
            const d = await res.json();

            $("#donation_id").val(d.id);
            $("#donor_name").val(d.donor_name);
            $("#resource_type").val(d.resource_type);
            $("#quantity").val(d.quantity);
            $("#unit").val(d.unit);
            $("#amount").val(d.amount);
            $("#disaster_id").val(d.disaster_id);

            $("#donationModal").modal("show");
        } catch (err) {
            console.error(err);
            showError("Failed to load donation details");
        }
    });

    // ---------------- Delete Donation ----------------
    $('#donationTable').on("click", ".deleteBtn", function () {
        const id = $(this).data("id");
        Swal.fire({
            title: "Are you sure?",
            text: "This donation will be permanently deleted.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, delete it!"
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/donation/${id}`, { method: "DELETE" });
                    const data = await res.json();
                    if (res.ok) showSuccess(data.message);
                    else showError(data.message || "Delete failed");

                    loadDonations();
                    debouncedReloadResources();
                } catch (err) {
                    console.error(err);
                    showError("Could not delete donation");
                }
            }
        });
    });
});
