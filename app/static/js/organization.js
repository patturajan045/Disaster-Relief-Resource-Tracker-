
document.addEventListener("DOMContentLoaded", () => {
  const orgCards    = document.getElementById("orgCards");
  const btnAddOrg   = document.getElementById("btnAddOrg");
  const searchInput = document.getElementById("searchInput");
  const filterType  = document.getElementById("filterType");

  let organizations = [];

  /* ---------- API Helper ---------- */
  async function apiFetch(url, options = {}) {
    const res  = await fetch(url, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed: ${res.status}`);
    return data;
  }

  /* ---------- Load & Render ---------- */
  async function loadOrganizations() {
    try {
      organizations = await apiFetch("/organization/api");

      // Fill filter dropdown
      const types = [...new Set(organizations.map(o => o.type))].sort();
      filterType.innerHTML = `<option value="">All Types</option>` +
        types.map(t => `<option value="${t}">${t}</option>`).join("");

      renderOrganizations();
    } catch (err) {
      console.error(err);
      orgCards.innerHTML = `<p class="text-danger">Failed to load organizations</p>`;
    }
  }

  function renderOrganizations() {
    const q   = searchInput.value.trim().toLowerCase();
    const typ = filterType.value;

    const filtered = organizations.filter(o =>
      o.name.toLowerCase().includes(q) &&
      (!typ || o.type === typ)
    );

    orgCards.innerHTML = filtered.length
      ? ""
      : `<p class="text-muted">No organizations found.</p>`;

    filtered.forEach(o => {
      orgCards.insertAdjacentHTML(
        "beforeend",
        `<div class="col-md-4 mb-4">
           <div class="card shadow-sm h-100">
             <div class="card-body">
               <h5 class="card-title"><i class="bi bi-building me-2"></i>${o.name}</h5>
               <p class="card-text">
                 <strong>Type:</strong> ${o.type}<br>
                 <strong>Contact:</strong> ${o.contact_number}<br>
                 <strong>Members:</strong> ${o.members_count || 0}<br>
                 <strong>Relief Camps:</strong> ${o.relief_camps_count || 0}
               </p>
             </div>
             <div class="card-footer d-flex justify-content-between">
               <button class="btn btn-sm btn-warning"
                       onclick="OrgUI.edit(${o.org_id},
                         '${encodeURIComponent(o.name)}',
                         '${encodeURIComponent(o.type)}',
                         '${encodeURIComponent(o.contact_number || "")}')">
                 <i class="bi bi-pencil"></i> Edit
               </button>
               <button class="btn btn-sm btn-danger"
                       onclick="OrgUI.remove(${o.org_id})">
                 <i class="bi bi-trash"></i> Delete
               </button>
             </div>
           </div>
         </div>`
      );
    });
  }

  /* ---------- CRUD with SweetAlert ---------- */
  async function addOrganization() {
    const { value: form } = await Swal.fire({
      title: "Add Organization",
      html: `
        <input type="text" id="swName" class="form-control mb-2" placeholder="Organization Name">
        <input type="text" id="swType" class="form-control mb-2" placeholder="Type">
        <input type="text" id="swContact" class="form-control mb-2" placeholder="Contact Number">`,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: "Save",
      preConfirm: () => {
        const name    = document.getElementById("swName").value.trim();
        const type    = document.getElementById("swType").value.trim();
        const contact = document.getElementById("swContact").value.trim();
        if (!name || !type || !contact) {
          Swal.showValidationMessage("All fields are required");
          return false;
        }
        return { name, type, contact_number: contact };
      }
    });
    if (!form) return;

    try {
      const res = await apiFetch("/organization/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });
      Swal.fire("✅ Saved!", res.message, "success");
      await loadOrganizations();
    } catch (err) {
      Swal.fire("❌ Error", err.message, "error");
    }
  }

  async function editOrganization(id, name, type, contact) {
    name    = decodeURIComponent(name);
    type    = decodeURIComponent(type);
    contact = decodeURIComponent(contact);

    const { value: form } = await Swal.fire({
      title: "Edit Organization",
      html: `
        <input type="text" id="swNameEdit" class="form-control mb-2" value="${name}">
        <input type="text" id="swTypeEdit" class="form-control mb-2" value="${type}">
        <input type="text" id="swContactEdit" class="form-control mb-2" value="${contact}">`,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: "Update",
      preConfirm: () => {
        const n = document.getElementById("swNameEdit").value.trim();
        const t = document.getElementById("swTypeEdit").value.trim();
        const c = document.getElementById("swContactEdit").value.trim();
        if (!n || !t || !c) {
          Swal.showValidationMessage("All fields are required");
          return false;
        }
        return { name: n, type: t, contact_number: c };
      }
    });
    if (!form) return;

    try {
      const res = await apiFetch(`/organization/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });
      Swal.fire("✅ Updated!", res.message, "success");
      await loadOrganizations();
    } catch (err) {
      Swal.fire("❌ Error", err.message, "error");
    }
  }

  async function deleteOrganization(id) {
    const result = await Swal.fire({
      title: "Are you sure?",
      text: "This action cannot be undone.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#d33",
      cancelButtonColor: "#6c757d",
      confirmButtonText: "Yes, delete it!"
    });
    if (!result.isConfirmed) return;

    try {
      const res = await apiFetch(`/organization/${id}`, { method: "DELETE" });
      Swal.fire("✅ Deleted!", res.message, "success");
      await loadOrganizations();
    } catch (err) {
      Swal.fire("❌ Error", err.message, "error");
    }
  }

  /* ---------- Bind Events ---------- */
  btnAddOrg.addEventListener("click", addOrganization);
  searchInput.addEventListener("input", renderOrganizations);
  filterType.addEventListener("change", renderOrganizations);

  // expose for inline onclick handlers
  window.OrgUI = { edit: editOrganization, remove: deleteOrganization };

  loadOrganizations();
});

