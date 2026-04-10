function addToCart(id) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    cart.push(id);
    localStorage.setItem("cart", JSON.stringify(cart));
    alert("Added to cart!");
    document.getElementById("cart-count").innerText = cart.length;
}