document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".qty-btn").forEach(button => {
        button.addEventListener("click", function () {
            const isIncrement = this.textContent.trim() === "+";
            const row = this.closest(".cart-card");

            // ✅ Correct IDs
            const productId = row.getAttribute("data-product-id");
            const cartId = row.getAttribute("data-cart-id");
            const size = row.getAttribute("data-size");
            const color = row.getAttribute("data-color");
            const image = row.getAttribute("data-image");

            const data = {
                id: productId,
                cart_id: cartId,
                qty: isIncrement ? 1 : -1,
                size: size,
                color: color,
                image: image
            };

            fetch("/add-to-cart/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify(data)
            })
            .then(async response => {
                if (response.status === 401) {
                    window.location.href = "/auth/login/";
                    return;
                }

                const data = await response.json();

                if (data.status === "unauthenticated") {
                    window.location.href = data.login_url || "/auth/login/";
                    return;
                } else if (data.status === "success") {
                    if (data.removed) {
                        // 🗑 remove item row if backend says deleted
                        row.remove();
                    } else {
                        // ✅ Update qty input
                        const qtyInput = row.querySelector("input[type='number']");
                        qtyInput.value = data.item_qty;

                        // ✅ Update item total
                        row.querySelector(".item-total").textContent = "₹" + data.item_total;
                    }

                    // ✅ Update summary
                    const summary = document.querySelector(".summary");
                    if (summary) {
                        const subtotalEl = summary.querySelector("p:nth-child(2)");
                        const totalEl = summary.querySelector("p strong");

                        if (subtotalEl) subtotalEl.textContent = "Subtotal: ₹" + data.subtotal;
                        if (totalEl) totalEl.textContent = "Total: ₹" + data.grand_total;
                    }

                    showToast(data.message, "success");
                } else {
                    alert("Error: " + (data.message || "Unknown error"));
                }
            })
            .catch(error => {
                console.error("Request failed:", error);
                alert("Something went wrong while updating cart.");
            });
        });
    });
});

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
