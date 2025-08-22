// cart.js — for Cart page increment/decrement

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".cart-card .qty-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const row = this.closest(".cart-card");
      if (!row) return;

      const itemId = row.getAttribute("data-id");   // CartItem.id
      const isInc = this.textContent.trim() === "+";
      const action = isInc ? "inc" : "dec";

      fetch("/update-cart-qty/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ item_id: itemId, action })
      })
      .then(res => res.json())
      .then(data => {
        if (data.status !== "success") {
          alert("Error: " + (data.message || "Could not update cart"));
          return;
        }

        // update qty
        const qtyInput = row.querySelector("input[type='number']");
        if (qtyInput) qtyInput.value = data.item_qty;

        // update item total
        const totalEl = row.querySelector(".item-total");
        if (totalEl) totalEl.textContent = "₹" + formatINR(data.item_total);

        // update summary
        document.querySelector(".summary").innerHTML = `
          <h3>Order Summary</h3>
          <p>Subtotal: ₹${formatINR(data.subtotal)}</p>
          <p>Free Shipping</p>
          <p>Tax: ₹0</p>
          <hr>
          <p><strong>Total: ₹${formatINR(data.grand_total)}</strong></p>
          <form action="/checkout/" method="get">
              <button type="submit" class="checkout-btn">Proceed To Checkout →</button>
          </form>
        `;
      })
      .catch(err => {
        console.error(err);
        alert("Something went wrong while updating the cart.");
      });
    });
  });
});

/* ---------- helpers ---------- */
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

function formatINR(val) {
  return Number(val).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}
