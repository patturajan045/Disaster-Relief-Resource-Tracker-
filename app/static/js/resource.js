document.addEventListener("DOMContentLoaded", function () {
    const resourceList = document.getElementById("resourceList");
    const resourceForm = document.getElementById("resourceForm");
    const resourceModalEl = document.getElementById("resourceModal");
    const resourceModal = new bootstrap.Modal(resourceModalEl);
    const searchInput = document.getElementById("searchInput");
    const filterType = document.getElementById("filterType");

    let allResources = [];

    // ---------------- SweetAlert2 ----------------
    const showSuccess = msg => Swal.fire({ icon: "success", title: "Success", text: msg, timer: 2000, showConfirmButton: false });
    const showError = msg => Swal.fire({ icon: "error", title: "Error", text: msg });
    const showConfirm = msg => Swal.fire({
        title: "Are you sure?",
        text: msg,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Yes, delete it!"
    });

    // ---------------- Debounce ----------------
    let reloadTimeout = null;
    function debouncedReload() {
        if (reloadTimeout) clearTimeout(reloadTimeout);
        reloadTimeout = setTimeout(fetchResources, 300); // wait 300ms
    }

    // ---------------- Type Colors & Icons ----------------
    const getTypeColor = type => {
        switch (type?.toLowerCase()) {
            case "relief": return "success";
            case "health": return "info";
            case "support": return "warning";
            case "contact": return "danger";
            case "donation": return "primary";
            default: return "secondary";
        }
    };

    const getTypeIcon = type => {
        switch (type?.toLowerCase()) {
            case "relief": return "bi-heart-fill";
            case "health": return "bi-activity";
            case "support": return "bi-gift-fill";
            case "contact": return "bi-telephone-fill";
            case "donation": return "bi-cash-coin";
            default: return "bi-box";
        }
    };

    // ---------------- Fetch Resources & Donations ----------------
    async function fetchResources() {
        try {
            const res = await fetch("/resources/api");
            if (!res.ok) throw new Error(`Status ${res.status}`);

            const data = await res.json();

            // Deduplicate by composite key: name + disaster_id + quantity + unit
            const seen = new Set();
            allResources = data.filter(item => {
                const key = `${item.name || item.donor_name}-${item.disaster_id}-${item.quantity}-${item.unit}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            }).map(item => ({
                id: item.id,
                name: item.name || item.donor_name || "Anonymous",
                donor_name: item.donor_name || item.name || "Anonymous",
                resource_type: item.resource_type || "resource",
                quantity: item.quantity || 0,
                unit: item.unit || "",
                disaster_id: item.disaster_id || "-",
                source: item.source || "resource",
            }));

            renderResources(allResources);
        } catch (err) {
            console.error(err);
            showError("Unable to fetch resources and donations.");
        }
    }


    // ---------------- Render Cards ----------------
    function renderResources(resources) {
        resourceList.innerHTML = "";
        resources.forEach(r => {
            const col = document.createElement("div");
            col.className = "col-md-4";

            const card = document.createElement("div");
            card.className = "card shadow-sm h-100 card-resource";
            card.innerHTML = `
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title mb-2">
                        <i class="bi ${getTypeIcon(r.resource_type)} me-2"></i>
                        ${r.donor_name || r.name || "Anonymous"}
                    </h5>
                    <p class="card-text mb-1">
                        <span class="badge bg-${getTypeColor(r.resource_type)}">
                            ${r.resource_type?.toUpperCase() || "-"}
                        </span>
                    </p>
                    <p class="card-text mb-1">
                        <i class="bi bi-box-seam me-1"></i>
                        <strong>Quantity:</strong> ${r.quantity} ${r.unit}
                    </p>
                    <p class="card-text mb-2">
                        <i class="bi bi-geo-alt me-1"></i>
                        <strong>Disaster ID:</strong> ${r.disaster_id}
                    </p>
                    <div class="mt-auto d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${r.id}">
                            <i class="bi bi-pencil-square"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${r.id}">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
            col.appendChild(card);
            resourceList.appendChild(col);
        });

        attachCardEvents();
    }

    function attachCardEvents() {
        document.querySelectorAll(".edit-btn").forEach(btn =>
            btn.removeEventListener("click", () => editResource(btn.dataset.id))
        );
        document.querySelectorAll(".edit-btn").forEach(btn =>
            btn.addEventListener("click", () => editResource(btn.dataset.id))
        );

        document.querySelectorAll(".delete-btn").forEach(btn =>
            btn.removeEventListener("click", () => deleteResource(btn.dataset.id))
        );
        document.querySelectorAll(".delete-btn").forEach(btn =>
            btn.addEventListener("click", async () => {
                const result = await showConfirm("This resource will be deleted!");
                if (result.isConfirmed) deleteResource(btn.dataset.id);
            })
        );
    }

    async function editResource(id) {
        try {
            const res = await fetch(`/resources/resource/${id}`);
            if (!res.ok) throw new Error(`Status ${res.status}`);
            const data = await res.json();

            resourceForm.dataset.editId = id;
            resourceForm.resourceName.value = data.name || data.donor_name || "";
            resourceForm.resourceType.value = data.resource_type || "";
            resourceForm.resourceQuantity.value = data.quantity || 0;
            resourceForm.resourceUnit.value = data.unit || "";
            resourceForm.resourceDisaster.value = data.disaster_id || "";

            document.getElementById("resourceModalLabel").textContent = "Edit Resource";
            resourceModal.show();
        } catch (err) {
            console.error(err);
            showError("Unable to load resource for editing");
        }
    }

    async function deleteResource(id) {
        try {
            const res = await fetch(`/resources/resource/${id}`, { method: "DELETE" });
            const result = await res.json();
            if (res.ok) showSuccess(result.message);
            else showError(result.message || "Error deleting resource");

            debouncedReload();
        } catch (err) {
            console.error(err);
            showError("Server error while deleting resource");
        }
    }

    resourceForm.addEventListener("submit", async e => {
        e.preventDefault();
        const id = resourceForm.dataset.editId;
        const payload = {
            name: resourceForm.resourceName.value,
            resource_type: resourceForm.resourceType.value,
            quantity: parseInt(resourceForm.resourceQuantity.value) || 0,
            unit: resourceForm.resourceUnit.value,
            disaster_id: parseInt(resourceForm.resourceDisaster.value) || null
        };

        try {
            const url = id ? `/resources/resource/${id}` : "/resources/create";
            const method = id ? "PUT" : "POST";

            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await res.json();
            if (res.ok) {
                showSuccess(result.message);
                resourceForm.reset();
                delete resourceForm.dataset.editId;

                debouncedReload();
                resourceModal.hide();
            } else {
                showError(result.error || result.message || "Error saving resource");
            }
        } catch (err) {
            console.error(err);
            showError("Server error while saving resource");
        }
    });

    searchInput.addEventListener("input", () => renderResources(applyFilters()));
    filterType.addEventListener("change", () => renderResources(applyFilters()));

    function applyFilters() {
        const typeValue = filterType.value.toLowerCase();
        const searchValue = searchInput.value.toLowerCase();

        return allResources.filter(r => {
            const baseName = r.name || r.donor_name || "";
            const matchesType = typeValue ? r.resource_type.toLowerCase() === typeValue : true;
            const matchesSearch = baseName.toLowerCase().includes(searchValue) ||
                (r.disaster_id && r.disaster_id.toString().includes(searchValue));
            return matchesType && matchesSearch;
        });
    }

    document.addEventListener("donation-changed", debouncedReload);

    fetchResources();
});
