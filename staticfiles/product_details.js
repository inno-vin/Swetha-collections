console.log("hey watsapp");

let selectedSize = "";
let selectedColor = "";

document.addEventListener("DOMContentLoaded", function () {
  const mainImage = document.getElementById("main-product-image");
  const zoomViewer = document.getElementById("zoom-viewer");
  const zoomLens = document.getElementById("zoom-lens");

  // ✅ Size Selection
  document.querySelectorAll(".size-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedSize = btn.getAttribute("data-size");
      document.getElementById("selected-size").value = selectedSize;
      document.querySelectorAll(".size-btn").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
    });
  });

  // ✅ Color Selection
  document.querySelectorAll(".color-box").forEach(box => {
    box.addEventListener("click", () => {
      selectedColor = box.getAttribute("data-color");
      const newImage = box.getAttribute("data-image");
      document.getElementById("selected-color").value = selectedColor;

      document.querySelectorAll(".color-box").forEach(b => b.classList.remove("selected"));
      box.classList.add("selected");

      if (newImage && mainImage) {
        mainImage.src = newImage;
      }

      document.querySelectorAll(".thumbnail").forEach(th => {
        const thumbFilename = th.src.split('/').pop();
        const colorFilename = newImage.split('/').pop();
        if (thumbFilename === colorFilename) {
          document.querySelectorAll(".thumbnail").forEach(t => t.classList.remove("active"));
          th.classList.add("active");
        }
      });
    });
  });

  // ✅ Thumbnail Hover
  document.querySelectorAll(".thumbnail").forEach(thumbnail => {
    thumbnail.addEventListener("click", function () {
      const clickedSrc = thumbnail.getAttribute("src");
      if (mainImage && clickedSrc) {
        mainImage.src = clickedSrc;
      }

      document.querySelectorAll(".thumbnail").forEach(t => t.classList.remove("active"));
      thumbnail.classList.add("active");
    });

    thumbnail.addEventListener("mouseenter", function () {
      const hoverSrc = thumbnail.getAttribute("src");
      if (mainImage && hoverSrc) {
        mainImage.src = hoverSrc;
      }

      document.querySelectorAll(".thumbnail").forEach(t => t.classList.remove("active"));
      thumbnail.classList.add("active");
    });
  });

  // ✅ Flipkart-style Instant Zoom with Lens
  if (mainImage && zoomViewer && zoomLens) {
    mainImage.addEventListener("mousemove", function (e) {
      const rect = mainImage.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const lensSize = 120;
      const lensX = Math.max(0, Math.min(x - lensSize / 2, rect.width - lensSize));
      const lensY = Math.max(0, Math.min(y - lensSize / 2, rect.height - lensSize));

      zoomLens.style.left = `${lensX}px`;
      zoomLens.style.top = `${lensY}px`;
      zoomLens.style.display = "block";

      zoomViewer.style.backgroundImage = `url(${mainImage.src})`;
      zoomViewer.style.backgroundSize = `${rect.width * 2}px ${rect.height * 2}px`;
      zoomViewer.style.backgroundPosition = `${(lensX / rect.width) * 100}% ${(lensY / rect.height) * 100}%`;
      zoomViewer.style.display = "block";
    });

    mainImage.addEventListener("mouseenter", () => {
      zoomLens.style.display = "block";
      zoomViewer.style.display = "block";
    });

    mainImage.addEventListener("mouseleave", () => {
      zoomLens.style.display = "none";
      zoomViewer.style.display = "none";
    });
  }

  // ✅ Add to Cart
  document.querySelectorAll(".add-to-cart").forEach(button => {
    button.addEventListener("click", function () {
      const productId = this.getAttribute("data-product-id");
      const qty = 1;

      let cartId = localStorage.getItem("cart_id");
      if (!cartId) {
        cartId = Math.random().toString(36).substr(2, 9);
        localStorage.setItem("cart_id", cartId);
      }

      const selectedImage = mainImage?.src || "";

      fetch(`/add-to-cart/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
          id: productId,
          qty: qty,
          cart_id: cartId,
          size: selectedSize,
          color: selectedColor,
          image: selectedImage
        })
      })
        .then(async response => {
          if (response.status === 401) {
            alert("Please log in to add items to cart.");
            window.location.href = "/auth/login/";
            return;
          }

          const data = await response.json();

          if (data.status === "unauthenticated") {
            window.location.href = data.login_url || "/auth/login/";
          } else if (data.status === "success") {
            showToast(data.message, "success");
            updateCartCount();
          } else {
            alert("Error: " + (data.message || "Something went wrong"));
          }
        })
        .catch(error => console.error("❌ Add to cart error:", error));
    });
  });

  // ✅ Wishlist Button Handling
document.querySelectorAll(".wishlist-btn, .wishlist-btn2")
.forEach(button => {
    button.addEventListener("click", function () {
      const productId = this.dataset.productId;
      const csrfToken = getCookie("csrftoken");

      fetch(`/wishlist/add/${productId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
      })
        .then(res => res.json())
        .then(data => {
          const icon = this.querySelector("i");

          if (data.status === "unauthenticated") {
            showToast("Please login to add to wishlist ❤️", "info");
            setTimeout(() => {
              window.location.href = "/auth/login/";
            }, 1500);
            return;
          }

          if (data.status === "success") {
            icon?.classList.add("text-danger");
            showToast("Added to wishlist ❤️", "success");
            updateWishlistCount();  // ✅ New line
          } else if (data.status === "removed") {
            icon?.classList.remove("text-danger");
            showToast("Removed from wishlist 💔", "info");
            updateWishlistCount();  // ✅ New line
          } else {
            showToast(data.message || "Something went wrong ❌", "error");
          }
        })
        .catch(err => {
          console.error("❌ Wishlist error:", err);
          showToast("Server error while updating wishlist ❌", "error");
        });
    });
  });

  // ✅ Update counts on page load
  updateCartCount();
  updateWishlistCount();
});

// ✅ CSRF Token Getter
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ✅ Cart Count
function updateCartCount() {
  fetch("/cart/count/")
    .then(res => res.json())
    .then(data => {
      const countElement = document.querySelector(".cart-count");
      if (countElement) {
        countElement.textContent = data.count;
      }
    });
}

// ✅ Wishlist Count
function updateWishlistCount() {
  fetch("/wishlist/count/")
    .then(res => res.json())
    .then(data => {
      const countElement = document.querySelector(".wishlist-count");
      if (countElement) {
        countElement.textContent = data.count;
      }
    });
}


