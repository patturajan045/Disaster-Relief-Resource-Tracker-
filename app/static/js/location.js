// ----------------------
// User Location Map Logic
// ----------------------
document.addEventListener("DOMContentLoaded", function () {

    // Initialize map
    const map = L.map('map').setView([20.5937, 78.9629], 5);
    const marker = L.marker([20.5937, 78.9629], { draggable: true }).addTo(map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Update marker and input fields
    function updateMarker(lat, lng, zoom = 10) {
        marker.setLatLng([lat, lng]);
        map.setView([lat, lng], zoom);
        document.getElementById("latitude").value = lat.toFixed(6);
        document.getElementById("longitude").value = lng.toFixed(6);
    }

    // ----------------------
    // Fetch saved location
    // ----------------------
    fetch('/')
        .then(res => {
            if (!res.ok) {
                if (res.status === 404) return null; // No location yet
                throw new Error("Unable to fetch location");
            }
            return res.json();
        })
        .then(data => {
            if (data && data.latitude && data.longitude) {
                updateMarker(data.latitude, data.longitude, 10);
            }
        })
        .catch(err => console.log("Error fetching location:", err));

    // ----------------------
    // Marker drag event
    // ----------------------
    marker.on('dragend', () => {
        const { lat, lng } = marker.getLatLng();
        updateMarker(lat, lng);
    });

    // ----------------------
    // Map click event
    // ----------------------
    map.on('click', (e) => {
        const { lat, lng } = e.latlng;
        updateMarker(lat, lng);
    });

    map.doubleClickZoom.disable();

    // ----------------------
    // Detect location button
    // ----------------------
    document.getElementById("detectLocation").addEventListener("click", () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(pos => {
                updateMarker(pos.coords.latitude, pos.coords.longitude, 13);
            }, () => showError("Unable to detect location"));
        } else {
            showError("Geolocation not supported");
        }
    });

    // ----------------------
    // Save location form
    // ----------------------
    document.getElementById("locationForm").addEventListener("submit", async (e) => {
        e.preventDefault();

        const lat = document.getElementById("latitude").value;
        const lng = document.getElementById("longitude").value;

        const spinner = document.getElementById("saveSpinner");
        spinner.classList.remove("d-none");

        try {
            const res = await fetch('/userLocation', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ latitude: lat, longitude: lng })
            });

            const result = await res.json();
            if (res.ok) showSuccess(result.message);
            else showError(result.message || "Error saving location");
        } catch (err) {
            showError("Server error");
        } finally {
            spinner.classList.add("d-none");
        }
    });

    // ----------------------
    // Alert messages
    // ----------------------
    function showSuccess(msg) {
        const el = document.getElementById("successAlert");
        el.innerText = msg;
        el.style.display = "block";
        setTimeout(() => el.style.display = "none", 3000);
    }

    function showError(msg) {
        const el = document.getElementById("errorAlert");
        el.innerText = msg;
        el.style.display = "block";
        setTimeout(() => el.style.display = "none", 4000);
    }

    // ----------------------
    // Sidebar toggle for mobile
    // ----------------------
    document.addEventListener("DOMContentLoaded", () => {
        const sidebar = document.getElementById("sidebar");
        const overlay = document.getElementById("overlay");
        const toggleBtn = document.getElementById("sidebarToggle");

        // Sidebar toggle
        toggleBtn?.addEventListener("click", () => {
            sidebar.classList.toggle("active");
            overlay.classList.toggle("active");
        });

        overlay?.addEventListener("click", () => {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
        });

        // Highlight active nav link
        const currentPath = window.location.pathname.replace(/\/$/, ""); // remove trailing slash
        document.querySelectorAll(".sidebar .nav-link").forEach(link => {
            const linkPath = link.getAttribute("href").replace(/\/$/, "");
            if (linkPath === currentPath) {
                link.classList.add("active");
            }
        });
    });
});
