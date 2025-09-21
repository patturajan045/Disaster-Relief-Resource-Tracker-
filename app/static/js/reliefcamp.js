const campContainer = document.getElementById("campContainer");
const searchInput = document.getElementById("searchInput");
const createCampForm = document.getElementById("createCampForm");
let campsData = [];

// ----------------------
// Fetch camps from API
// ----------------------
async function fetchCamps() {
    try {
        const res = await fetch("/reliefCamp/api");
        if (!res.ok) throw new Error("Failed to fetch camps");
        campsData = await res.json();
        renderCamps(campsData);
    } catch (err) {
        Swal.fire("❌ Error", err.message, "error");
    }
}

// ----------------------
// Render camps as cards
// ----------------------
function renderCamps(camps) {
    campContainer.innerHTML = "";

    if (!camps.length) {
        campContainer.innerHTML = `<p class="text-center text-muted">No camps found</p>`;
        return;
    }

    camps.forEach(camp => {
        campContainer.insertAdjacentHTML("beforeend", `
          <div class="col">
            <div class="card camp-card shadow-sm rounded-3 h-100">
              <div class="card-body">
                <h5 class="card-title text-primary d-flex align-items-center">
                  <i class="bi bi-house-door-fill me-2 text-success"></i> ${camp.name}
                </h5>
                <p class="card-text small text-muted">
                  <i class="bi bi-geo-alt-fill text-danger me-1"></i> ${camp.location}<br>
                  <i class="bi bi-people-fill text-info me-1"></i> Capacity: <b>${camp.capacity}</b><br>
                  <i class="bi bi-person-check-fill text-warning me-1"></i> Occupancy: <b>${camp.current_occupancy}</b>
                </p>
                <div class="d-flex justify-content-between">
                  <button class="btn btn-sm btn-outline-primary" onclick="openEditCamp(${camp.id})">
                    <i class="bi bi-pencil-square me-1"></i> Edit
                  </button>
                  <button class="btn btn-sm btn-outline-danger" onclick="deleteCamp(${camp.id}, '${camp.name}')">
                    <i class="bi bi-trash me-1"></i> Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        `);
    });
}

// ----------------------
// Delete camp
// ----------------------
async function deleteCamp(campId, campName) {
    Swal.fire({
        title: `Delete "${campName}"?`,
        text: "This action cannot be undone!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Yes, delete it!"
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const res = await fetch(`/reliefCamp/${campId}`, {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ admin_email: "admin@example.com" })
                });
                if (!res.ok) throw new Error("Failed to delete camp");

                const result = await res.json();
                Swal.fire("✅ Deleted!", result.message, "success");
                fetchCamps();
            } catch (err) {
                Swal.fire("❌ Error", err.message, "error");
            }
        }
    });
}

// ----------------------
// Create camp (modal form)
// ----------------------
createCampForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(createCampForm);
    const data = Object.fromEntries(formData.entries());

    data.capacity = parseInt(data.capacity, 10);
    data.current_occupancy = parseInt(data.current_occupancy || 0, 10);

    try {
        const res = await fetch("/reliefCamp/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to create camp");

        const result = await res.json();
        Swal.fire("✅ Success", result.message, "success");

        fetchCamps();
        createCampForm.reset();
        bootstrap.Modal.getInstance(document.getElementById("createCampModal")).hide();
    } catch (err) {
        Swal.fire("❌ Error", err.message, "error");
    }
});

// ----------------------
// Open Edit Modal
// ----------------------
function openEditCamp(campId) {
    const camp = campsData.find(c => c.id === campId);
    if (!camp) return;

    // build modal dynamically (reuse if exists)
    let modal = document.getElementById("editCampModal");
    if (!modal) {
        document.body.insertAdjacentHTML("beforeend", `
        <div class="modal fade" id="editCampModal" tabindex="-1">
          <div class="modal-dialog">
            <div class="modal-content">
              <form id="editCampForm">
                <div class="modal-header">
                  <h5 class="modal-title"><i class="bi bi-pencil-square me-2"></i>Edit Relief Camp</h5>
                  <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                  <input type="hidden" id="editCampId" name="id">
                  <div class="mb-2">
                    <label class="form-label">Camp Name</label>
                    <input type="text" class="form-control" id="editCampName" name="name" required>
                  </div>
                  <div class="mb-2">
                    <label class="form-label">Location</label>
                    <input type="text" class="form-control" id="editCampLocation" name="location" required>
                  </div>
                  <div class="mb-2">
                    <label class="form-label">Capacity</label>
                    <input type="number" class="form-control" id="editCampCapacity" name="capacity" required>
                  </div>
                  <div class="mb-2">
                    <label class="form-label">Current Occupancy</label>
                    <input type="number" class="form-control" id="editCampOccupancy" name="current_occupancy">
                  </div>
                </div>
                <div class="modal-footer">
                  <button type="submit" class="btn btn-primary">
                    <i class="bi bi-save me-1"></i> Update
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>`);
        modal = document.getElementById("editCampModal");

        // attach submit once
        document.getElementById("editCampForm").addEventListener("submit", submitEditCamp);
    }

    // fill form
    document.getElementById("editCampId").value = camp.id;
    document.getElementById("editCampName").value = camp.name;
    document.getElementById("editCampLocation").value = camp.location;
    document.getElementById("editCampCapacity").value = camp.capacity;
    document.getElementById("editCampOccupancy").value = camp.current_occupancy;

    new bootstrap.Modal(modal).show();
}

// ----------------------
// Handle Edit Submit
// ----------------------
async function submitEditCamp(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    data.capacity = parseInt(data.capacity, 10);
    data.current_occupancy = parseInt(data.current_occupancy || 0, 10);

    try {
        const res = await fetch(`/reliefCamp/${data.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to update camp");

        const result = await res.json();
        Swal.fire("✅ Updated", result.message, "success");

        fetchCamps();
        bootstrap.Modal.getInstance(document.getElementById("editCampModal")).hide();
    } catch (err) {
        Swal.fire("❌ Error", err.message, "error");
    }
}

// ----------------------
// Search filter
// ----------------------
searchInput.addEventListener("input", () => {
    const term = searchInput.value.toLowerCase();
    const filtered = campsData.filter(c =>
        c.name.toLowerCase().includes(term) ||
        c.location.toLowerCase().includes(term)
    );
    renderCamps(filtered);
});

// ----------------------
// Init
// ----------------------
fetchCamps();
