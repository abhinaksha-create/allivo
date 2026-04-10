import sqlite3

conn = sqlite3.connect("site.db")
cur = conn.cursor()

cur.execute("PRAGMA foreign_keys = ON")

cur.executescript("""
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS saved_addresses;
DROP TABLE IF EXISTS wishlist;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    password TEXT NOT NULL,
    address TEXT,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    subcategory TEXT,
    brand TEXT,
    price REAL NOT NULL,
    discount REAL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    image TEXT,
    description TEXT,
    delivery_type TEXT NOT NULL,
    rating REAL DEFAULT 0.0,
    is_student_pick INTEGER DEFAULT 0,
    refill_days INTEGER,
    product_code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    order_status TEXT DEFAULT 'placed',
    order_number TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    delivery_type TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(user_id, product_id)
);

CREATE TABLE saved_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    label TEXT,
    full_address TEXT NOT NULL,
    city TEXT,
    state TEXT,
    pincode TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    method_type TEXT NOT NULL,
    provider_name TEXT,
    display_value TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

# categories
categories = [
    ("Groceries", "Daily food and grocery items"),
    ("Clothing", "Fashion and wearable items"),
    ("Daily Essentials", "Personal and household essentials"),
    ("Stationery", "Books, notebooks, pens, and academic supplies")
]
cur.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)

# sample admin user
cur.execute("""
INSERT INTO users (full_name, username, email, phone, password, address, is_admin)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    "Admin User",
    "admin",
    "sadvi@gmail.com",
    "9999999999",
    "pbkdf2:sha256:600000$demo$abcdefghijklmnopqrstuv",  # temporary dummy hash
    "Hyderabad",
    1
))

# sample products
products = [
    ("Milk 1L", 1, "Dairy", "Amul", 30.0, 0.0, 100, "images/products/milk.jpg", "Fresh toned milk", "instant", 4.3, 1, 2, "PRD001"),
    ("Paneer 100g", 1, "Dairy", "Amul", 120.0, 0.0, 50, "images/products/paneer.webp", "Fresh paneer", "instant", 4.4, 1, 2, "PRD002"),
    ("Men Cotton T-Shirt", 2, "T-Shirts", "Roadster", 399.0, 50.0, 40, "images/products/tshirt.webp", "Comfortable cotton t-shirt", "scheduled", 4.2, 1, None, "PRD003"),
    ("Shampoo 180ml", 3, "Hair Care", "Clinic Plus", 120.0, 10.0, 60, "images/products/shampoo.jpg", "Hair shampoo for daily use", "instant", 4.1, 1, 25, "PRD004"),
    ("Classmate Notebook 200 Pages", 4, "Stationery", "Classmate", 75.0, 10.0, 50, "images/products/book.webp", "Classmate long notebook", "instant", 4.4, 1, 4, "PRD005")
]

cur.executemany("""
INSERT INTO products (
    name, category_id, subcategory, brand, price, discount, stock, image,
    description, delivery_type, rating, is_student_pick, refill_days, product_code
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", products)

conn.commit()
conn.close()

print("SQLite database created successfully: site.db")