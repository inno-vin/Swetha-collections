console.log("📋 account.js loaded");

document.addEventListener("DOMContentLoaded", function () {
  const navLinks = document.querySelectorAll(".nav-link[data-target]");
  const tabs = document.querySelectorAll(".tab");

  function showTab(targetId) {
    tabs.forEach(tab => tab.classList.remove("active"));
    navLinks.forEach(link => link.classList.remove("active"));

    const activeTab = document.getElementById(targetId);
    const activeLink = document.querySelector(`.nav-link[data-target="${targetId}"]`);

    if (activeTab && activeLink) {
      activeTab.classList.add("active");
      activeLink.classList.add("active");

      if (targetId === "address") setupAddressValidation();
    }
  }

  function setupAddressValidation() {
    const form = document.querySelector("#address-form");
    if (form && !form.dataset.listenerAttached) {
      form.addEventListener("submit", function (e) {
        const address = form.querySelector('input[name="address"]').value.trim();
        const city = form.querySelector('input[name="city"]').value.trim();
        const pin = form.querySelector('input[name="postal_code"]').value.trim();

        if (!address || !city || !pin) {
          alert("Please either use 'My Location' or fill your address manually.");
          e.preventDefault();
        }
      });
      form.dataset.listenerAttached = "true";
    }
  }

  // Auto-open tab from URL ?tab=wishlist etc.
  const params = new URLSearchParams(window.location.search);
  const defaultTab = params.get("tab");
  if (defaultTab) {
    showTab(defaultTab);
  } else {
    showTab("dashboard"); // Fallback
  }

  // Tab switching click
  navLinks.forEach(link => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      showTab(this.dataset.target);
    });
  });

  // Profile form submit handler
  const profileForm = document.querySelector("#profile form");
  if (profileForm) {
    profileForm.addEventListener("submit", function () {
      const newName = profileForm.querySelector('input[name="name"]').value.trim();
      const newMobile = profileForm.querySelector('input[name="mobile"]').value.trim();
      const newAvatar = profileForm.querySelector('input[name="avatar"]').files[0];

      if (newName) {
        const nameElem = document.querySelector(".avatar h3");
        if (nameElem) nameElem.textContent = newName;
      }

      if (newAvatar) {
        const avatarImg = document.querySelector(".avatar img");
        const reader = new FileReader();
        reader.onload = function (e) {
          avatarImg.src = e.target.result;
        };
        reader.readAsDataURL(newAvatar);
      }

      const addressMobile = document.querySelector('#address input[name="mobile"]');
      if (addressMobile && newMobile) {
        addressMobile.value = newMobile;
      }

      alert("✅ Profile updated successfully.");
    });
  }

  // Toggle password change form
  const togglePasswordBtn = document.getElementById("toggle-password-form");
  const passwordForm = document.getElementById("password-form");

  if (togglePasswordBtn && passwordForm) {
    togglePasswordBtn.addEventListener("click", function (e) {
      e.preventDefault();
      passwordForm.style.display = passwordForm.style.display === "none" ? "block" : "none";
    });
  }
  // Handle "View Order" button clicks in dashboard
  document.querySelectorAll(".view-order-btn").forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();

      const orderId = this.getAttribute("data-order-id");

      // Switch to Orders tab
      showTab("orders");

      // Scroll to that specific order after a small delay
      setTimeout(() => {
        const orderElement = document.getElementById("order-" + orderId);
        if (orderElement) {
          orderElement.scrollIntoView({ behavior: "smooth", block: "start" });
          orderElement.style.backgroundColor = "#fff8d6"; // highlight
          setTimeout(() => orderElement.style.backgroundColor = "", 2000);
        }
      }, 200); // Delay ensures tab is visible before scrolling
    });
  });

});

// ---------------- Get Location (OpenStreetMap; no Google key) ----------------
window.getLocation = function () {
  console.log("📍 getLocation() called");
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      showPosition,
      showError,
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  } else {
    alert("Geolocation is not supported by this browser.");
  }
};

async function showPosition(position) {
  const lat = position.coords.latitude;
  const lon = position.coords.longitude;

  try {
    // Reverse geocode with OpenStreetMap (Nominatim) — no API key needed
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&addressdetails=1`
    );
    const data = await res.json();

    if (!data || !data.address) {
      alert("❌ Could not fetch your address. Please fill it manually.");
      return;
    }

    const a = data.address || {};
    const formatted   = data.display_name || "";
    const city        = a.city || a.town || a.village || a.suburb || a.county || "";
    const state       = a.state || "";
    const postcode    = a.postcode || "";
    const country     = a.country || "";

    // Fill your existing inputs by name
    const q = (n) => document.querySelector(`input[name="${n}"]`);
    if (q("address"))     q("address").value     = formatted;
    if (q("city"))        q("city").value        = city;
    if (q("state"))       q("state").value       = state;
    if (q("postal_code")) q("postal_code").value = postcode;
    if (q("country"))     q("country").value     = country;
  } catch (err) {
    console.error("❌ Error fetching address:", err);
    alert("❌ Network error while fetching address.");
  }
}

function showError(error) {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      alert("Permission denied.");
      break;
    case error.POSITION_UNAVAILABLE:
      alert("Location unavailable.");
      break;
    case error.TIMEOUT:
      alert("Request timed out.");
      break;
    case error.UNKNOWN_ERROR:
      alert("Unknown error.");
      break;
  }
}
