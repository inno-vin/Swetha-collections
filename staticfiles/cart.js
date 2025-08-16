document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".qty-btn").forEach(button => {
        button.addEventListener("click", function () {
            const isIncrement = this.textContent.trim() === "+";
            const row = this.closest(".cart-card");

            const itemId = row.getAttribute("data-id");
            const size = row.getAttribute("data-size");
            const color = row.getAttribute("data-color");
            const image = row.getAttribute("data-image");

            const data = {
                id: itemId,
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
                   showToast(data.message, "success");
                } else {
                    alert("Error: " + (data.message || "Unknown error"));
                }
            })
            .catch(error => {
                console.error("Request failed:", error);
                alert("Something went wrong while adding to cart.");
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
