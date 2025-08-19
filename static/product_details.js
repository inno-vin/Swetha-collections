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

  // --- ✅ Instagram Share/Copy (outside add-to-cart) ---
  const igLink = document.getElementById("ig-share-link");
  const productUrl = igLink ? igLink.dataset.url : window.location.href;
  const productName = typeof window.PRODUCT_NAME !== "undefined" ? window.PRODUCT_NAME : "{{ product.name|escapejs }}";

  function _ensureToast() {
    if (typeof window.showToast === "function") return;
    let t = document.getElementById("share-toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "share-toast";
      t.className = "share-toast";
      t.setAttribute("role", "status");
      t.setAttribute("aria-live", "polite");
      t.style.cssText = "position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);background:rgba(0,0,0,.85);color:#fff;padding:8px 12px;border-radius:999px;font-size:14px;opacity:0;pointer-events:none;transition:all .25s ease;z-index:9999;";
      document.body.appendChild(t);
    }
    window.showToast = function (msg = "Link copied!") {
      const el = document.getElementById("share-toast");
      el.textContent = msg;
      el.style.opacity = "1";
      el.style.transform = "translateX(-50%) translateY(0)";
      setTimeout(() => {
        el.style.opacity = "0";
        el.style.transform = "translateX(-50%) translateY(20px)";
      }, 1600);
    };
  }

  async function _copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      (window.showToast || (()=>{}))("Link copied!");
    } catch (e) {
      console.error(e);
      (window.showToast || (()=>{}))("Couldn't copy. Long-press to copy.");
    }
  }

  if (igLink) {
    _ensureToast();
    igLink.addEventListener("click", async (e) => {
      e.preventDefault();

      // 1) Mobile: native share sheet (user can pick Instagram)
      if (navigator.share) {
        try {
          await navigator.share({
            title: productName,
            text: "Check this out:",
            url: productUrl
          });
          return;
        } catch (err) {
          // user canceled or share failed; continue to copy + open IG
        }
      }

      // 2) Copy link so user can paste in IG DM
      await _copyToClipboard(productUrl);

      // 3) Try to open Instagram app DMs
      let opened = false;
      try {
        const w = window.open("instagram://direct", "_blank");
        if (w) opened = true;
      } catch (_) {}

      // 4) Fallback to Instagram web DMs
      if (!opened) {
        window.open("https://www.instagram.com/direct/new/", "_blank");
      }
    });
  }

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
