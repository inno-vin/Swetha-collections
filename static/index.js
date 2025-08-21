console.log("hey watsapp");
console.log("Wishlist script ready");

// -------------------- UTILITY --------------------
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `advanced-toast ${type}`;

    const iconMap = {
        success: "✅",
        error: "⛔",
        info: "🔔"
    };

    const icon = document.createElement("span");
    icon.className = "toast-icon";
    icon.textContent = iconMap[type] || "🔔";

    const text = document.createElement("span");
    text.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(text);

    toast.addEventListener("click", () => {
        toast.classList.remove("visible");
        setTimeout(() => toast.remove(), 300);
    });

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add("visible");
    });

    setTimeout(() => {
        toast.classList.remove("visible");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// -------------------- DOM READY --------------------
document.addEventListener("DOMContentLoaded", () => {

   // -------------------- Wishlist Button Handler --------------------
   document.querySelectorAll(".wishlist-btn, .wishlist-btn2")
.forEach(btn => {
        btn.addEventListener("click", function () {
            const productId = this.dataset.productId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            fetch(`/wishlist/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            })
            .then(res => res.text())
            .then(text => {
                try {
                    console.log("Server response:", text);  // Optional debug log
                    const data = JSON.parse(text);

                    if (data.status === "unauthenticated") {
                        showToast("Please login to add to wishlist ❤️", "info");
                        setTimeout(() => {
                            window.location.href = "/auth/login/";
                        }, 2000);
                        return;
                    }

                    if (data.status === "success") {
                        showToast("Added to Wishlist ❤️", "success");
                        const wishlistCount = document.getElementById("wishlist-count");
                        if (wishlistCount) {
                            wishlistCount.textContent = (parseInt(wishlistCount.textContent) || 0) + 1;
                        }
                    } else {
                        showToast(data.message || "Something went wrong ❌", "error");
                    }

                } catch (err) {
                    console.error("Unexpected response:", text);
                    showToast("Server error while updating wishlist ❌", "error");
                }
            })
            .catch(err => {
                console.error("Network error:", err);
                showToast("Network error ❌", "error");
            });
        });
    });

});



let slideIndex = 0;
showSlides();

function showSlides() {
    let slides = document.getElementsByClassName("mySlides");
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";  
    }
    slideIndex++;
    if (slideIndex > slides.length) {slideIndex = 1}    
    slides[slideIndex - 1].style.display = "block";  
    setTimeout(showSlides, 3000); // Change image every 3 seconds
}


document.addEventListener("click", (e) => {
  const btn = e.target.closest(".add-to-cart, .wishlist-btn");
  if (!btn) return;

  if (document.body.dataset.loggedIn !== "true") {
    e.preventDefault();
    window.location.href = document.body.dataset.loginUrl;
  }
});
