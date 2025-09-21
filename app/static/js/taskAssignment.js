const taskContainer = document.getElementById("taskContainer");
const createTaskForm = document.getElementById("createTaskForm");
let tasksData = [];

// Status → Badge color mapping
const statusColors = {
  "Assigned": "secondary",
  "In Progress": "warning",
  "Completed": "success"
};

// -------------------- API Helper --------------------
async function apiRequest(url, method = "GET", body = null) {
  try {
    const options = { method, headers: { "Content-Type": "application/json" } };
    if (body) options.body = JSON.stringify(body);

    const res = await fetch(url, options);
    if (!res.ok) {
      const errMsg = await res.text();
      throw new Error(errMsg || "Request failed");
    }
    return await res.json();
  } catch (err) {
    Swal.fire("❌ Error", err.message, "error");
    throw err;
  }
}

// -------------------- Fetch & Render --------------------
async function fetchTasks() {
  try {
    tasksData = await apiRequest("/taskAssignment/api");
    renderTasks(tasksData);
  } catch (_) {
    // handled by apiRequest
  }
}

function renderTasks(tasks) {
  taskContainer.innerHTML = "";

  if (!tasks.length) {
    taskContainer.innerHTML = `<p class="text-center text-muted">No tasks found</p>`;
    return;
  }

  tasks.forEach(t => {
    const badgeColor = statusColors[t.status] || "info";
    taskContainer.insertAdjacentHTML("beforeend", `
      <div class="col-md-4 mb-3">
        <div class="card shadow-sm rounded-3 h-100">
          <div class="card-body">
            <h6 class="card-title">
              <i class="bi bi-person me-2"></i> Volunteer #${t.volunteer_id}
            </h6>
            <p class="card-text">
              <i class="bi bi-file-earmark-text me-1"></i> Request ID: <b>${t.relief_request_id}</b><br>
              <i class="bi bi-info-circle me-1"></i> Status: 
              <span class="badge bg-${badgeColor}">${t.status}</span><br>
              <i class="bi bi-clock me-1"></i> Assigned: ${new Date(t.assigned_at).toLocaleString()}
            </p>
            <div class="d-flex justify-content-between">
              <button class="btn btn-sm btn-outline-warning" onclick="updateTask(${t.id}, '${t.status}')">
                <i class="bi bi-pencil-square"></i> Edit
              </button>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteTask(${t.id})">
                <i class="bi bi-trash"></i> Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    `);
  });
}

// -------------------- Create --------------------
createTaskForm.addEventListener("submit", async e => {
  e.preventDefault();
  const formData = new FormData(createTaskForm);
  const data = Object.fromEntries(formData.entries());
  data.admin_id = 1; // Replace with session user ID

  try {
    const result = await apiRequest("/taskAssignment/", "POST", data);
    Swal.fire("✅ Success", result.message, "success");
    fetchTasks();
    createTaskForm.reset();
    bootstrap.Modal.getInstance(document.getElementById("createTaskModal")).hide();
  } catch (_) {
    // handled by apiRequest
  }
});

// -------------------- Update --------------------
async function updateTask(taskId, currentStatus) {
  const { value: status } = await Swal.fire({
    title: "Update Task Status",
    input: "select",
    inputOptions: {
      "Assigned": "Assigned",
      "In Progress": "In Progress",
      "Completed": "Completed"
    },
    inputValue: currentStatus,
    showCancelButton: true
  });

  if (status && status !== currentStatus) {
    try {
      await apiRequest(`/taskAssignment/${taskId}`, "PUT", { admin_id: 1, status });
      Swal.fire("✅ Updated", "Task status updated", "success");
      fetchTasks();
    } catch (_) { }
  }
}

// -------------------- Delete --------------------
async function deleteTask(taskId) {
  const result = await Swal.fire({
    title: "Are you sure?",
    text: "This task will be permanently deleted.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Yes, delete it!",
    confirmButtonColor: "#d33"
  });

  if (result.isConfirmed) {
    try {
      await apiRequest(`/taskAssignment/${taskId}`, "DELETE", { admin_id: 1 });
      Swal.fire("✅ Deleted", "Task removed successfully", "success");
      fetchTasks();
    } catch (_) { }
  }
}

// -------------------- Init --------------------
fetchTasks();
