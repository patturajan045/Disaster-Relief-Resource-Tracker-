document.addEventListener("DOMContentLoaded", () => {
    const profileDiv = document.getElementById("volunteerProfile");
    const form = document.getElementById("volunteerForm");
    const deleteBtn = document.getElementById("deleteBtn");

    // Convert form data to JSON
    function formToJSON(formEl) {
        const formData = new FormData(formEl);
        let data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });
        data["availability"] = formEl.querySelector("[name=availability]").checked;
        return data;
    }

    // Load current profile
    async function loadProfile() {
        try {
            const res = await fetch("/volunteer/me");
            const data = await res.json();

            if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

            if (data.error) {
                if (data.error.includes("not a volunteer")) {
                    Swal.fire({
                        icon: "error",
                        title: "Access Denied",
                        text: "You are not a volunteer, so you cannot create a volunteer profile!",
                        confirmButtonColor: "#d33"
                    });
                    form.style.display = "none";
                } else {
                    profileDiv.innerHTML = `<div class="alert alert-warning">No profile found.</div>`;
                }
                return;
            }


            profileDiv.innerHTML = `
    <div class="card shadow border-0 rounded-3">
        <div class="card-header bg-light d-flex justify-content-between align-items-center">
            <h6 class="mb-0">👤 My Volunteer Profile</h6>
            <button id="editProfile" class="btn btn-sm btn-outline-primary"> Edit</button>
        </div>
        <div class="card-body">
            <div class="row g-3">
                <div class="col-md-6">
                    <p class="mb-1 text-muted">Skills</p>
                    <h6>${data.skills || "-"}</h6>
                </div>
                <div class="col-md-6">
                    <p class="mb-1 text-muted">Experience</p>
                    <h6>${data.experience_years ? data.experience_years + " years" : "-"}</h6>
                </div>
                <div class="col-md-6">
                    <p class="mb-1 text-muted">Location</p>
                    <h6>${data.location || "-"}</h6>
                </div>
                <div class="col-md-6">
                    <p class="mb-1 text-muted">Preferred Role</p>
                    <h6>${data.preferred_role || "-"}</h6>
                </div>
                <div class="col-md-6">
                    <p class="mb-1 text-muted">Languages</p>
                    <h6>${data.languages || "-"}</h6>
                </div>
                <div class="col-md-6">
                    <p class="mb-1 text-muted">Phone</p>
                    <h6>${data.phone_number || "-"}</h6>
                </div>
                <div class="col-12">
                    <p class="mb-1 text-muted">Availability</p>
                    <h6>${data.availability ? "✅ Available" : "❌ Not Available"}</h6>
                </div>
            </div>
        </div>
    </div>
`;


            // Fill form fields
            for (let key in data) {
                const input = form.querySelector(`[name=${key}]`);
                if (input) {
                    if (input.type === "checkbox") {
                        input.checked = !!data[key];
                    } else {
                        input.value = data[key] || "";
                    }
                }
            }
        } catch (err) {
            console.error("Error loading profile:", err);
            Swal.fire({
                icon: "error",
                title: "Failed to Load",
                text: "Unable to load volunteer profile. Please try again later."
            });
        }
    }

    // Save (create/update)
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = formToJSON(form);

        try {
            const res = await fetch("/volunteer/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                Swal.fire({
                    icon: "success",
                    title: "Profile Saved",
                    text: "Your volunteer profile has been saved successfully!",
                    timer: 2000,
                    showConfirmButton: false
                });
                loadProfile();
            } else {
                Swal.fire({
                    icon: "error",
                    title: "Save Failed",
                    text: data.error || "Could not save profile."
                });
            }
        } catch (err) {
            console.error("Error saving profile:", err);
            Swal.fire({
                icon: "error",
                title: "Save Failed",
                text: "Something went wrong while saving your profile."
            });
        }
    });

    // Delete profile
    deleteBtn.addEventListener("click", async () => {
        Swal.fire({
            title: "Are you sure?",
            text: "This will permanently delete your profile.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#3085d6",
            confirmButtonText: "Yes, delete it!"
        }).then(async (result) => {
            if (!result.isConfirmed) return;

            try {
                const res = await fetch("/volunteer/delete", { method: "DELETE" });
                const data = await res.json();

                if (res.ok) {
                    Swal.fire({
                        icon: "success",
                        title: "Deleted!",
                        text: "Your volunteer profile has been deleted."
                    });
                    form.reset();
                    profileDiv.innerHTML = `<div class="alert alert-info">Profile deleted.</div>`;
                } else {
                    Swal.fire({
                        icon: "error",
                        title: "Delete Failed",
                        text: data.error || "Could not delete profile."
                    });
                }
            } catch (err) {
                console.error("Error deleting profile:", err);
                Swal.fire({
                    icon: "error",
                    title: "Delete Failed",
                    text: "Something went wrong while deleting your profile."
                });
            }
        });
    });

    // Initial load
    loadProfile();
});
