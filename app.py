import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from utils.auth import login_required, admin_required
from flask_mail import Mail, Message
from utils.budget_helper import build_budget_query
from utils.refill_helper import build_refill_query
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from utils.auth import login_required, admin_required
import os
from flask_mail import Mail,Message
from utils.budget_helper import build_budget_query
from utils.refill_helper import build_refill_query


app = Flask(__name__)
app.config.from_object(Config)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "images", "products")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
mail = Mail(app)

def get_sqlite_connection():
    if "sqlite_conn" not in g:
        g.sqlite_conn = sqlite3.connect(app.config["SQLITE_DB"])
        g.sqlite_conn.execute("PRAGMA foreign_keys = ON")
    return g.sqlite_conn


@app.teardown_appcontext
def close_sqlite_connection(exception=None):
    conn = g.pop("sqlite_conn", None)
    if conn is not None:
        conn.close()


class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("%s", "?")
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        return self

    def executemany(self, query, param_list):
        query = query.replace("%s", "?")
        self.cursor.executemany(query, param_list)
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount


class SQLiteConnectionWrapper:
    def cursor(self):
        return SQLiteCursorWrapper(get_sqlite_connection().cursor())

    def commit(self):
        get_sqlite_connection().commit()

    def rollback(self):
        get_sqlite_connection().rollback()

    def close(self):
        pass


class SQLiteMySQLCompat:
    @property
    def connection(self):
        return SQLiteConnectionWrapper()


mysql = SQLiteMySQLCompat()

@app.route("/test-email")
def test_email():
    send_email(
        "sadvii025@gmail.com",
        "Test Email from Allivo",
        """
        <h2>Hello from Allivo</h2>
        <p>This is a test email.</p>
        """
    )
    return "Test email sent. Check inbox/spam."

def send_email(to_email, subject, html_body):
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email]
        )
        msg.html = html_body
        mail.send(msg)
        print("Email sent successfully")
        return True
    except Exception as e:
        print("Email error:", e)
        return False

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            p.id,
            p.name,
            c.name AS category_name,
            p.price,
            p.discount,
            p.image
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
        LIMIT 6
    """)
    products = cur.fetchall()
    cur.close()

    return render_template("home.html", products=products)

@app.route("/products")
def products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    cur = mysql.connection.cursor()

    query = """
        SELECT 
            p.id, p.name, c.name AS category_name, p.subcategory, p.brand,
            p.price, p.discount, p.stock, p.image, p.description,
            p.delivery_type, p.rating, p.is_student_pick, p.refill_days
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (p.name LIKE %s OR p.brand LIKE %s OR p.subcategory LIKE %s)"
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    if category:
        query += " AND c.name = %s"
        params.append(category)

    query += " ORDER BY p.id DESC"

    cur.execute(query, tuple(params))
    all_products = cur.fetchall()

    cur.execute("SELECT name FROM categories ORDER BY name")
    categories = cur.fetchall()

    wishlist_ids = []
    if "user_id" in session:
        cur.execute("""
            SELECT product_id
            FROM wishlist
            WHERE user_id = %s
        """, (session["user_id"],))
        wishlist_ids = [row[0] for row in cur.fetchall()]

    cur.close()

    return render_template(
        "products.html",
        products=all_products,
        categories=categories,
        selected_category=category,
        search=search,
        wishlist_ids=wishlist_ids
    )
@app.route("/product/<int:product_id>")
def product_details(product_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            p.id, p.name, c.name AS category_name, p.subcategory, p.brand,
            p.price, p.discount, p.stock, p.image, p.description,
            p.delivery_type, p.rating, p.is_student_pick, p.refill_days
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = %s
    """, (product_id,))
    product = cur.fetchone()

    if not product:
        cur.close()
        flash("Product not found", "danger")
        return redirect(url_for("products"))

    cur.execute("""
        SELECT 
            p.id, p.name, p.price, p.discount, p.image
        FROM products p
        WHERE p.id != %s
        ORDER BY p.id DESC
        LIMIT 4
    """, (product_id,))
    related_products = cur.fetchall()

    wishlist_ids = []
    if "user_id" in session:
        cur.execute("""
            SELECT product_id
            FROM wishlist
            WHERE user_id = %s
        """, (session["user_id"],))
        wishlist_ids = [row[0] for row in cur.fetchall()]

    cur.close()

    return render_template(
        "product_details.html",
        product=product,
        related_products=related_products,
        wishlist_ids=wishlist_ids
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic validation
        if not full_name or not username or not email or not phone or not password or not confirm_password:
            flash("All fields are required", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))

        cur = mysql.connection.cursor()

        # Check duplicate email
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_email = cur.fetchone()

        if existing_email:
            cur.close()
            flash("Email already exists", "danger")
            return redirect(url_for("register"))

        # Check duplicate username
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing_username = cur.fetchone()

        if existing_username:
            cur.close()
            flash("Username already exists", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        is_admin = 0

        cur.execute("""
            INSERT INTO users (full_name, username, email, phone, password, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (full_name, username, email, phone, hashed_password, is_admin))

        mysql.connection.commit()
        cur.close()

        # Send welcome email
        send_email(
            email,
            "Welcome to Allivo",
            f"""
            <div style="font-family: Arial; padding: 20px; background:#f6f8fc;">
                <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:12px;">
                    
                    <h2 style="color:#2563eb;">Welcome to Allivo 🎉</h2>

                    <p>Hi <strong>{full_name}</strong>,</p>

                    <p>Your account has been created successfully.</p>

                    <p>Start exploring smart shopping with Allivo.</p>

                    <a href="http://127.0.0.1:5000"
                       style="display:inline-block;margin-top:15px;padding:12px 20px;
                       background:#2563eb;color:white;text-decoration:none;border-radius:8px;">
                       Start Shopping
                    </a>

                    <p style="margin-top:30px;color:#6b7280;">Regards,<br>Allivo Team</p>
                </div>
            </div>
            """
        )

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")
       


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, full_name, username, email, phone, password, address, is_admin
            FROM users
            WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[5], password):
            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["username"] = user[2]
            session["is_admin"] = user[7]

            flash("Login successful", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, quantity
        FROM cart_items
        WHERE user_id = %s AND product_id = %s
    """, (user_id, product_id))
    existing_item = cur.fetchone()

    if existing_item:
        cur.execute("""
            UPDATE cart_items
            SET quantity = quantity + 1
            WHERE id = %s
        """, (existing_item[0],))
    else:
        cur.execute("""
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
        """, (user_id, product_id, 1))

    mysql.connection.commit()
    cur.close()

    flash("Product added to cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            ci.id, ci.quantity,
            p.id, p.name, p.price, p.discount, p.image, p.delivery_type, p.stock
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = %s
    """, (user_id,))
    cart_rows = cur.fetchall()
    cur.close()

    instant_items = []
    scheduled_items = []
    total = 0

    for row in cart_rows:
        cart_item_id = row[0]
        quantity = row[1]
        product_id = row[2]
        name = row[3]
        price = float(row[4])
        discount = float(row[5])
        image = row[6]
        delivery_type = row[7]
        stock = row[8]

        final_price = price - discount
        subtotal = final_price * quantity
        total += subtotal

        item_data = {
            "cart_item_id": cart_item_id,
            "product_id": product_id,
            "name": name,
            "price": price,
            "discount": discount,
            "final_price": final_price,
            "image": image,
            "delivery_type": delivery_type,
            "stock": stock,
            "quantity": quantity,
            "subtotal": subtotal
        }

        if delivery_type == "instant":
            instant_items.append(item_data)
        else:
            scheduled_items.append(item_data)

    return render_template(
        "cart.html",
        instant_items=instant_items,
        scheduled_items=scheduled_items,
        total=total
    )

@app.route("/increase_quantity/<int:cart_item_id>")
def increase_quantity(cart_item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE cart_items
        SET quantity = quantity + 1
        WHERE id = %s AND user_id = %s
    """, (cart_item_id, session["user_id"]))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for("cart"))


@app.route("/decrease_quantity/<int:cart_item_id>")
def decrease_quantity(cart_item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    # get current quantity
    cur.execute("""
        SELECT quantity FROM cart_items
        WHERE id = %s AND user_id = %s
    """, (cart_item_id, session["user_id"]))

    item = cur.fetchone()

    if item:
        if item[0] > 1:
            cur.execute("""
                UPDATE cart_items
                SET quantity = quantity - 1
                WHERE id = %s
            """, (cart_item_id,))
        else:
            # remove item if quantity = 1
            cur.execute("""
                DELETE FROM cart_items
                WHERE id = %s
            """, (cart_item_id,))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for("cart"))

@app.route("/remove_from_cart/<int:cart_item_id>")
def remove_from_cart(cart_item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM cart_items
        WHERE id = %s AND user_id = %s
    """, (cart_item_id, session["user_id"]))
    mysql.connection.commit()
    cur.close()

    flash("Item removed from cart", "info")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    # cart items
    cur.execute("""
        SELECT 
            ci.id, ci.quantity,
            p.id, p.name, p.price, p.discount, p.image, p.delivery_type
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = %s
    """, (user_id,))
    cart_rows = cur.fetchall()

    if not cart_rows:
        cur.close()
        flash("Your cart is empty", "warning")
        return redirect(url_for("products"))

    # saved addresses
    cur.execute("""
        SELECT id, label, full_address, city, state, pincode
        FROM saved_addresses
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user_id,))
    saved_addresses = cur.fetchall()

    items = []
    total = 0

    for row in cart_rows:
        quantity = row[1]
        name = row[3]
        price = float(row[4])
        discount = float(row[5])
        image = row[6]
        delivery_type = row[7]

        final_price = price - discount
        subtotal = final_price * quantity
        total += subtotal

        items.append({
            "name": name,
            "price": price,
            "discount": discount,
            "final_price": final_price,
            "image": image,
            "delivery_type": delivery_type,
            "quantity": quantity,
            "subtotal": subtotal
        })

    if request.method == "POST":
        selected_address_id = request.form.get("saved_address_id")
        manual_address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        payment_method = request.form.get("payment_method")

        final_address = None

        if selected_address_id:
            cur.execute("""
                SELECT full_address, city, state, pincode
                FROM saved_addresses
                WHERE id = %s AND user_id = %s
            """, (selected_address_id, user_id))
            saved = cur.fetchone()

            if saved:
                final_address = f"{saved[0]}, {saved[1]}, {saved[2]} - {saved[3]}"

        if not final_address:
            final_address = manual_address

        if not final_address or not phone or not payment_method:
            flash("Please fill all required checkout fields", "danger")
            cur.close()
            return redirect(url_for("checkout"))

        cur.execute("""
            INSERT INTO orders (user_id, total_amount, address, phone, payment_method, order_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, total, final_address, phone, payment_method, "placed"))
        mysql.connection.commit()

        order_id = cur.lastrowid
        order_number = f"ORD{order_id:04d}"

        cur.execute("""
            UPDATE orders
            SET order_number = %s
            WHERE id = %s
        """, (order_number, order_id))

        for row in cart_rows:
            quantity = row[1]
            product_id = row[2]
            price = float(row[4])
            discount = float(row[5])
            delivery_type = row[7]
            final_price = price - discount

            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price, delivery_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, product_id, quantity, final_price, delivery_type))

        cur.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()

        if payment_method == "cod":
            flash("Order placed successfully", "success")
            return redirect(url_for("orders"))
        else:
            flash("Proceed to complete your payment", "info")
            return redirect(url_for("payment_gateway", order_id=order_id))
    

    cur.close()
    return render_template(
        "checkout.html",
        items=items,
        total=total,
        saved_addresses=saved_addresses
    )

@app.route("/payment-gateway/<int:order_id>", methods=["GET", "POST"])
def payment_gateway(order_id):
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, order_number, total_amount, payment_method, order_status
        FROM orders
        WHERE id = %s AND user_id = %s
    """, (order_id, session["user_id"]))
    order = cur.fetchone()

    cur.close()

    if not order:
        flash("Order not found", "danger")
        return redirect(url_for("orders"))

    if request.method == "POST":
        flash("Payment successful. Your order has been confirmed.", "success")
        return redirect(url_for("orders"))

    return render_template("payment_gateway.html", order=order)

@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, order_number, total_amount, order_status, created_at
        FROM orders
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user_id,))

    orders = cur.fetchall()
    cur.close()

    return render_template("orders.html", orders=orders)


@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, full_name, username, email, phone, is_admin
        FROM users
        WHERE id = %s
    """, (session["user_id"],))
    user = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE user_id = %s
    """, (session["user_id"],))
    total_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM cart_items
        WHERE user_id = %s
    """, (session["user_id"],))
    total_cart_items = cur.fetchone()[0]

    cur.close()

    return render_template(
        "profile.html",
        user=user,
        total_orders=total_orders,
        total_cart_items=total_cart_items
    )
@app.route("/buy_again/<int:order_id>")
def buy_again(order_id):
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id
        FROM orders
        WHERE id = %s AND user_id = %s
    """, (order_id, user_id))
    order = cur.fetchone()

    if not order:
        cur.close()
        flash("Order not found", "danger")
        return redirect(url_for("orders"))

    cur.execute("""
        SELECT oi.product_id, oi.quantity, p.stock
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cur.fetchall()

    added_any = False

    for product_id, quantity, stock in items:
        if stock <= 0:
            continue

        qty_to_add = min(quantity, stock)

        cur.execute("""
            SELECT id
            FROM cart_items
            WHERE user_id = %s AND product_id = %s
        """, (user_id, product_id))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE cart_items
                SET quantity = quantity + %s
                WHERE id = %s
            """, (qty_to_add, existing[0]))
        else:
            cur.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, product_id, qty_to_add))

        added_any = True

    mysql.connection.commit()
    cur.close()

    if added_any:
        flash("Available items from the order were added to cart", "success")
    else:
        flash("No available items could be added to cart", "warning")

    return redirect(url_for("cart"))

@app.route("/wishlist")

def wishlist():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            w.id, p.id, p.name, p.price, p.discount, p.image, p.brand
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = %s
        ORDER BY w.id DESC
    """, (session["user_id"],))
    wishlist_items = cur.fetchall()
    cur.close()

    return render_template("wishlist.html", wishlist_items=wishlist_items)



@app.route("/add-to-wishlist/<int:product_id>")
def add_to_wishlist(product_id):
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id
        FROM wishlist
        WHERE user_id = %s AND product_id = %s
    """, (user_id, product_id))
    existing = cur.fetchone()

    if existing:
        cur.execute("""
            DELETE FROM wishlist
            WHERE id = %s
        """, (existing[0],))
        mysql.connection.commit()
        flash("Removed from wishlist", "info")
    else:
        cur.execute("""
            INSERT INTO wishlist (user_id, product_id)
            VALUES (%s, %s)
        """, (user_id, product_id))
        mysql.connection.commit()
        flash("Added to wishlist", "success")

    cur.close()
    return redirect(request.referrer or url_for("products"))

@app.route("/remove-from-wishlist/<int:wishlist_id>")
def remove_from_wishlist(wishlist_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM wishlist
        WHERE id = %s AND user_id = %s
    """, (wishlist_id, session["user_id"]))
    mysql.connection.commit()
    cur.close()

    flash("Removed from wishlist", "info")
    return redirect(url_for("wishlist"))

@app.route("/move-wishlist-to-cart/<int:product_id>")
def move_wishlist_to_cart(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, quantity
        FROM cart_items
        WHERE user_id = %s AND product_id = %s
    """, (user_id, product_id))
    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE cart_items
            SET quantity = quantity + 1
            WHERE id = %s
        """, (existing[0],))
    else:
        cur.execute("""
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (%s, %s, 1)
        """, (user_id, product_id))

    mysql.connection.commit()
    cur.close()

    flash("Moved to cart", "success")
    return redirect(url_for("wishlist"))

@app.route("/saved-addresses", methods=["GET", "POST"])
@app.route("/saved-addresses", methods=["GET", "POST"])
def saved_addresses():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    if request.method == "POST":
        label = request.form.get("label")
        full_address = request.form.get("full_address")
        city = request.form.get("city")
        state = request.form.get("state")
        pincode = request.form.get("pincode")

        cur.execute("""
            INSERT INTO saved_addresses (user_id, label, full_address, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session["user_id"], label, full_address, city, state, pincode))
        mysql.connection.commit()
        flash("Address saved successfully", "success")

    cur.execute("""
        SELECT id, label, full_address, city, state, pincode
        FROM saved_addresses
        WHERE user_id = %s
        ORDER BY id DESC
    """, (session["user_id"],))
    addresses = cur.fetchall()
    cur.close()

    return render_template("saved_addresses.html", addresses=addresses)

@app.route("/delete-address/<int:address_id>")
def delete_address(address_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM saved_addresses
        WHERE id = %s AND user_id = %s
    """, (address_id, session["user_id"]))
    mysql.connection.commit()
    cur.close()

    flash("Address removed", "info")
    return redirect(url_for("saved_addresses"))

@app.route("/payment-methods", methods=["GET", "POST"])
def payment_methods():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    if request.method == "POST":
        method_type = request.form.get("method_type")
        provider_name = request.form.get("provider_name")
        display_value = request.form.get("display_value")
        is_default = 1 if request.form.get("is_default") else 0

        if not method_type or not display_value:
            flash("Please fill required fields", "danger")
            cur.close()
            return redirect(url_for("payment_methods"))

        if is_default:
            cur.execute("""
                UPDATE payment_methods
                SET is_default = 0
                WHERE user_id = %s
            """, (session["user_id"],))

        cur.execute("""
            INSERT INTO payment_methods (user_id, method_type, provider_name, display_value, is_default)
            VALUES (%s, %s, %s, %s, %s)
        """, (session["user_id"], method_type, provider_name, display_value, is_default))

        mysql.connection.commit()
        flash("Payment method added successfully", "success")

    cur.execute("""
        SELECT id, method_type, provider_name, display_value, is_default
        FROM payment_methods
        WHERE user_id = %s
        ORDER BY is_default DESC, id DESC
    """, (session["user_id"],))
    methods = cur.fetchall()
    cur.close()

    return render_template("payment_methods.html", methods=methods)

@app.route("/delete-payment-method/<int:method_id>")
def delete_payment_method(method_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM payment_methods
        WHERE id = %s AND user_id = %s
    """, (method_id, session["user_id"]))
    mysql.connection.commit()
    cur.close()

    flash("Payment method removed", "info")
    return redirect(url_for("payment_methods"))

@app.route("/set-default-payment/<int:method_id>")
def set_default_payment(method_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE payment_methods
        SET is_default = 0
        WHERE user_id = %s
    """, (session["user_id"],))

    cur.execute("""
        UPDATE payment_methods
        SET is_default = 1
        WHERE id = %s AND user_id = %s
    """, (method_id, session["user_id"]))

    mysql.connection.commit()
    cur.close()

    flash("Default payment method updated", "success")
    return redirect(url_for("payment_methods"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")

        cur.execute("""
            UPDATE users
            SET full_name = %s, username = %s, email = %s, phone = %s
            WHERE id = %s
        """, (full_name, username, email, phone, session["user_id"]))
        mysql.connection.commit()

        session["full_name"] = full_name
        session["username"] = username

        flash("Profile updated successfully", "success")

    cur.execute("""
        SELECT id, full_name, username, email, phone
        FROM users
        WHERE id = %s
    """, (session["user_id"],))
    user = cur.fetchone()
    cur.close()

    return render_template("settings.html", user=user)

@app.route("/budget")
def budget():
    budget_value = request.args.get("budget", "").strip()
    category = request.args.get("category", "").strip()

    suggested_products = []
    cur = mysql.connection.cursor()

    if budget_value:
        try:
            budget_amount = float(budget_value)

            query, extra_params = build_budget_query(category)
            params = [budget_amount] + extra_params

            cur.execute(query, tuple(params))
            suggested_products = cur.fetchall()

        except ValueError:
            flash("Please enter a valid budget amount", "danger")

    cur.close()

    return render_template(
        "budget.html",
        suggested_products=suggested_products,
        selected_budget=budget_value,
        selected_category=category
    )

    return render_template(
        "budget.html",
        suggested_products=suggested_products,
        selected_budget=budget_value,
        selected_category=category
    )
@app.route("/student-mode")
def student_mode():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            p.id, p.name, c.name AS category_name, p.subcategory, p.brand,
            p.price, p.discount, p.stock, p.image, p.description,
            p.delivery_type, p.rating, p.is_student_pick, p.refill_days
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.is_student_pick = 1
        ORDER BY (p.price - p.discount) ASC
    """)
    products = cur.fetchall()
    cur.close()

    return render_template("student_mode.html", products=products)

@app.route("/refill")
def refill():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    query = build_refill_query()
    cur.execute(query)
    refill_products = cur.fetchall()
    cur.close()

    return render_template("refill.html", refill_products=refill_products)


@app.route("/admin")
def admin_dashboard():
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.close()

    return render_template(
        "admin_dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        total_users=total_users
    )

@app.route("/admin/add-product", methods=["GET", "POST"])
def add_product():

    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form["name"]
        category_id = request.form["category_id"]
        subcategory = request.form["subcategory"]
        brand = request.form["brand"]
        price = request.form["price"]
        discount = request.form["discount"] or 0
        stock = request.form["stock"]
        description = request.form["description"]
        delivery_type = request.form["delivery_type"]
        rating = request.form["rating"] or 0
        refill_days = request.form["refill_days"] or None
        is_student_pick = 1 if request.form.get("is_student_pick") else 0

        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Save file
            filepath = os.path.join('static/images/products', filename)
            file.save(filepath)

            image_path = f"images/products/{filename}"

        else:
            image_path = None

        cur.execute("""
        INSERT INTO products
        (name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
        name, category_id, subcategory, brand, price, discount, stock,
        image_path, description, delivery_type, rating, is_student_pick, refill_days
        ))

        product_id = cur.lastrowid
        product_code = f"PRD{product_id:03d}"

        cur.execute("""
        UPDATE products
        SET product_code = %s
        WHERE id = %s
        """, (product_code, product_id))

        mysql.connection.commit()
        cur.close()

        flash("Product added successfully", "success")
        return redirect(url_for("admin_dashboard"))

    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()

    return render_template("add_product.html", categories=categories)

@app.route("/admin/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form["name"]
        subcategory = request.form["subcategory"]
        brand = request.form["brand"]
        price = request.form["price"]
        discount = request.form["discount"] or 0
        stock = request.form["stock"]
        description = request.form["description"]
        delivery_type = request.form["delivery_type"]
        rating = request.form["rating"] or 0
        refill_days = request.form["refill_days"] or None
        is_student_pick = 1 if request.form.get("is_student_pick") else 0

        cur.execute("SELECT image FROM products WHERE id = %s", (product_id,))
        old_product = cur.fetchone()
        old_image = old_product[0] if old_product else None

        file = request.files.get("image")

        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_path = f"images/products/{filename}"
        else:
            image_path = old_image

        cur.execute("""
            UPDATE products
            SET name=%s, subcategory=%s, brand=%s, price=%s, discount=%s,
                stock=%s, image=%s, description=%s, delivery_type=%s,
                rating=%s, is_student_pick=%s, refill_days=%s
            WHERE id=%s
        """, (
            name, subcategory, brand, price, discount, stock, image_path,
            description, delivery_type, rating, is_student_pick, refill_days, product_id
        ))

        mysql.connection.commit()
        cur.close()

        flash("Product updated successfully", "success")
        return redirect(url_for("manage_products"))

    cur.execute("""
        SELECT id, name, category_id, subcategory, brand, price, discount, stock,
               image, description, delivery_type, rating, is_student_pick, refill_days
        FROM products
        WHERE id = %s
    """, (product_id,))
    product = cur.fetchone()
    cur.close()

    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("manage_products"))

    return render_template("edit_product.html", product=product)

@app.route("/admin/delete-product/<int:product_id>")
def delete_product(product_id):
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    mysql.connection.commit()
    cur.close()

    flash("Product deleted successfully", "info")
    return redirect(url_for("manage_products"))

@app.route("/admin/manage-products")
def manage_products():
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            p.id, p.name, c.name AS category_name, p.subcategory, p.brand,
            p.price, p.discount, p.stock, p.image, p.description,
            p.delivery_type, p.rating, p.is_student_pick, p.refill_days
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
    """)
    products = cur.fetchall()
    cur.close()

    return render_template("manage_products.html", products=products)

@app.route("/admin/manage-orders")
def manage_orders():
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, order_number, user_id, total_amount, address, phone, payment_method, order_status, created_at
        FROM orders
        ORDER BY id DESC
    """)
    orders = cur.fetchall()
    cur.close()

    return render_template("manage_orders.html", orders=orders)

@app.route("/admin/update-order-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    check = admin_required()
    if check:
        return check

    new_status = request.form["order_status"]
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT o.id, o.order_number, o.order_status, u.full_name, u.email
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = %s
    """, (order_id,))
    order_data = cur.fetchone()

    if not order_data:
        cur.close()
        flash("Order not found", "danger")
        return redirect(url_for("manage_orders"))

    old_status = order_data[2]
    order_number = order_data[1] or f"ORD{order_id:04d}"
    full_name = order_data[3]
    email = order_data[4]

    cur.execute("""
        UPDATE orders
        SET order_status = %s
        WHERE id = %s
    """, (new_status, order_id))
    mysql.connection.commit()
    cur.close()

    if old_status != "delivered" and new_status == "delivered":
        send_email(
            email,
            "Order Delivered - Allivo",
            f"""
            <div style="font-family: Arial; padding: 20px; background:#f6f8fc;">
                <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:12px;">
                    <h2 style="color:#059669;">Order Delivered ✅</h2>
                    <p>Hi <strong>{full_name}</strong>,</p>
                    <p>Your order <strong>{order_number}</strong> has been delivered successfully.</p>
                    <p>Thank you for shopping with Allivo.</p>
                    <p style="margin-top:30px;color:#6b7280;">Regards,<br>Allivo Team</p>
                </div>
            </div>
            """
        )

    flash("Order status updated", "success")
    return redirect(url_for("manage_orders"))

@app.route("/admin/manage-categories", methods=["GET", "POST"])
def manage_categories():
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]

        cur.execute("""
            INSERT INTO categories (name, description)
            VALUES (%s, %s)
        """, (name, description))
        mysql.connection.commit()

        flash("Category added successfully", "success")

    cur.execute("SELECT id, name, description FROM categories ORDER BY id DESC")
    categories = cur.fetchall()
    cur.close()

    return render_template("manage_categories.html", categories=categories)

@app.route("/admin/edit-category/<int:category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        cur.execute("""
            UPDATE categories
            SET name = %s, description = %s
            WHERE id = %s
        """, (name, description, category_id))
        mysql.connection.commit()
        cur.close()

        flash("Category updated successfully", "success")
        return redirect(url_for("manage_categories"))

    cur.execute("""
        SELECT id, name, description
        FROM categories
        WHERE id = %s
    """, (category_id,))
    category = cur.fetchone()
    cur.close()

    if not category:
        flash("Category not found", "danger")
        return redirect(url_for("manage_categories"))

    return render_template("edit_category.html", category=category)

@app.route("/admin/delete-category/<int:category_id>")
def delete_category(category_id):
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    mysql.connection.commit()
    cur.close()

    flash("Category deleted successfully", "info")
    return redirect(url_for("manage_categories"))

@app.route("/admin/manage-users")
def manage_users():
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, full_name, username, email, is_admin, created_at
        FROM users
        ORDER BY id DESC
    """)
    users = cur.fetchall()
    cur.close()

    return render_template("manage_users.html", users=users)

@app.route("/admin/make-admin/<int:user_id>")
def make_admin(user_id):
    check = admin_required()
    if check:
        return check

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE users
        SET is_admin = 1
        WHERE id = %s
    """, (user_id,))
    mysql.connection.commit()
    cur.close()

    flash("User promoted to admin", "success")
    return redirect(url_for("manage_users"))


@app.route("/admin/remove-admin/<int:user_id>")
def remove_admin(user_id):
    check = admin_required()
    if check:
        return check

    # avoid removing yourself by mistake if you want
    if session.get("user_id") == user_id:
        flash("You cannot remove your own admin access here", "danger")
        return redirect(url_for("manage_users"))

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE users
        SET is_admin = 0
        WHERE id = %s
    """, (user_id,))
    mysql.connection.commit()
    cur.close()

    flash("Admin access removed", "info")
    return redirect(url_for("manage_users"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, full_name, username, email, phone, password, address, is_admin
            FROM users
            WHERE email = %s AND is_admin = 1
        """, (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[5], password):
            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["username"] = user[2]
            session["is_admin"] = user[7]

            flash("Admin login successful", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials", "danger")

    return render_template("admin_login.html")

@app.route("/order/<int:order_id>")
def order_details(order_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, order_number, total_amount, address, phone,
               payment_method, order_status, created_at
        FROM orders
        WHERE id = %s AND user_id = %s
    """, (order_id, session["user_id"]))
    order = cur.fetchone()

    cur.execute("""
        SELECT p.id, oi.quantity, oi.price, oi.delivery_type, p.name, p.image
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (order_id,))
    order_items = cur.fetchall()

    cur.close()

    if not order:
        flash("Order not found", "danger")
        return redirect(url_for("orders"))

    return render_template(
        "order_details.html",
        order=order,
        order_items=order_items,
        order_status=order[6]
    )

if __name__ == "__main__":
    app.run(debug=True)
