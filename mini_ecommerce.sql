CREATE DATABASE mini_ecommerce;
use mini_ecommerce;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    password VARCHAR(255) NOT NULL,
    address TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category_id INT NOT NULL,
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    stock INT NOT NULL DEFAULT 0,
    image VARCHAR(255),
    description TEXT,
    delivery_type ENUM('instant', 'scheduled') NOT NULL,
    rating DECIMAL(2,1) DEFAULT 0.0,
    is_student_pick BOOLEAN DEFAULT FALSE,
    refill_days INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(15) NOT NULL,
    payment_method ENUM('cod', 'upi', 'card') NOT NULL,
    order_status ENUM('placed', 'packed', 'out_for_delivery', 'delivered') DEFAULT 'placed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    delivery_type ENUM('instant', 'scheduled') NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_wishlist_item (user_id, product_id)
);

CREATE TABLE saved_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    label VARCHAR(50),
    full_address TEXT NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    method_type ENUM('upi', 'card', 'cod') NOT NULL,
    provider_name VARCHAR(100),
    display_value VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
INSERT INTO categories (name, description) VALUES
('Groceries', 'Daily food and grocery items'),
('Clothing', 'Fashion and wearable items'),
('Daily Essentials', 'Personal and household essentials'),
('Stationery', 'Books, notebooks, pens, and academic supplies');

UPDATE users
set is_admin=1 where email='sadvi@gmail.com';

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Basmati Rice 5kg', (SELECT id FROM categories WHERE name='Groceries'), 'Rice', 'India Gate', 450.00, 20.00, 50, 'images/products/rice.jpg', 'Premium basmati rice', 'instant', 4.5, 0, 30),
('Milk 1L', (SELECT id FROM categories WHERE name='Groceries'), 'Dairy', 'Amul', 30.00, 0.00, 100, 'images/products/milk.jpg', 'Fresh toned milk', 'instant', 4.3, 1, 2),
('Paneer 100g', (SELECT id FROM categories WHERE name='Groceries'), 'Dairy', 'Amul', 120.00, 0.00, 50, 'images/products/paneer.webp', 'Fresh paneer', 'instant', 4.4, 1, 2),
('Butter 500g', (SELECT id FROM categories WHERE name='Groceries'), 'Dairy', 'Amul', 250.00, 10.00, 40, 'images/products/butter.webp', 'Salted butter', 'instant', 4.6, 1, 5),
('Brown Bread', (SELECT id FROM categories WHERE name='Groceries'), 'Bakery', 'Britannia', 40.00, 0.00, 90, 'images/products/bread.jpg', 'Healthy brown bread', 'instant', 4.1, 0, 2),
('Eggs 12pcs', (SELECT id FROM categories WHERE name='Groceries'), 'Dairy', 'Local Farm', 70.00, 0.00, 80, 'images/products/eggs.jpg', 'Fresh farm eggs', 'instant', 4.3, 1, 3),
('Potato Chips 200g', (SELECT id FROM categories WHERE name='Groceries'), 'Snacks', 'Lays', 50.00, 5.00, 100, 'images/products/chips.webp', 'Crispy salted chips', 'instant', 4.2, 1, 10),
('Biscuits 300g', (SELECT id FROM categories WHERE name='Groceries'), 'Snacks', 'Good Day', 60.00, 5.00, 90, 'images/products/biscuits.webp', 'Butter biscuits', 'instant', 4.4, 1, 15),
('Instant Noodles Pack', (SELECT id FROM categories WHERE name='Groceries'), 'Ready Food', 'Maggi', 70.00, 10.00, 120, 'images/products/noodles.webp', '2-minute noodles', 'instant', 4.6, 1, 20),
('Tea Powder 500g', (SELECT id FROM categories WHERE name='Groceries'), 'Beverages', 'Tata Tea', 250.00, 20.00, 40, 'images/products/tea.webp', 'Strong tea leaves', 'instant', 4.5, 0, 30),
('Coffee 200g', (SELECT id FROM categories WHERE name='Groceries'), 'Beverages', 'Nescafe', 320.00, 25.00, 35, 'images/products/coffee.webp', 'Instant coffee powder', 'instant', 4.6, 1, 30),
('Soft Drink 2L', (SELECT id FROM categories WHERE name='Groceries'), 'Beverages', 'Coca Cola', 95.00, 10.00, 60, 'images/products/softdrink.webp', 'Carbonated soft drink', 'instant', 4.3, 0, 7),
('Bananas 1 Dozen', (SELECT id FROM categories WHERE name='Groceries'), 'Fruits', 'Local Farm', 60.00, 0.00, 70, 'images/products/banana.webp', 'Fresh bananas', 'instant', 4.3, 1, 3),
('Tomatoes 1kg', (SELECT id FROM categories WHERE name='Groceries'), 'Vegetables', 'Local Farm', 40.00, 5.00, 80, 'images/products/tomato.webp', 'Fresh red tomatoes', 'instant', 4.2, 0, 3),
('Onions 1kg', (SELECT id FROM categories WHERE name='Groceries'), 'Vegetables', 'Local Farm', 35.00, 5.00, 85, 'images/products/onion.jpeg', 'Fresh onions', 'instant', 4.1, 0, 5);

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Men Cotton T-Shirt', (SELECT id FROM categories WHERE name='Clothing'), 'T-Shirts', 'Roadster', 399.00, 50.00, 40, 'images/products/tshirt.webp', 'Comfortable cotton t-shirt', 'scheduled', 4.2, 1, NULL),
('Women Casual Kurti', (SELECT id FROM categories WHERE name='Clothing'), 'Ethnic Wear', 'Libas', 799.00, 100.00, 25, 'images/products/kurti.webp', 'Stylish casual kurti', 'scheduled', 4.4, 0, NULL),
('Men Formal Shirt', (SELECT id FROM categories WHERE name='Clothing'), 'Shirts', 'Peter England', 999.00, 150.00, 30, 'images/products/formalshirt.webp', 'Formal office shirt', 'scheduled', 4.5, 0, NULL),
('Women Saree', (SELECT id FROM categories WHERE name='Clothing'), 'Ethnic Wear', 'Kalini', 1299.00, 200.00, 20, 'images/products/saree.webp', 'Traditional saree', 'scheduled', 4.6, 1, NULL),
('Men Sports Shoes', (SELECT id FROM categories WHERE name='Clothing'), 'Footwear', 'Nike', 2499.00, 300.00, 15, 'images/products/shoes.jpeg', 'Comfortable running shoes', 'scheduled', 4.7, 1, NULL),
('Men Casual Shirt', (SELECT id FROM categories WHERE name='Clothing'), 'Shirts', 'Roadster', 699.00, 100.00, 35, 'images/products/men_casual_shirt.webp', 'Casual cotton shirt', 'scheduled', 4.3, 1, NULL),
('Men Hoodie', (SELECT id FROM categories WHERE name='Clothing'), 'Winter Wear', 'HRX', 1299.00, 200.00, 20, 'images/products/men_hoodie.webp', 'Warm hooded sweatshirt', 'scheduled', 4.5, 1, NULL),
('Men Track Pants', (SELECT id FROM categories WHERE name='Clothing'), 'Sportswear', 'Adidas', 1199.00, 150.00, 25, 'images/products/trackpants.webp', 'Comfortable track pants', 'scheduled', 4.4, 0, NULL),
('Men Kurta', (SELECT id FROM categories WHERE name='Clothing'), 'Ethnic Wear', 'FabIndia', 999.00, 120.00, 30, 'images/products/men_kurta.webp', 'Traditional cotton kurta', 'scheduled', 4.6, 1, NULL),
('Women Maxi Dress', (SELECT id FROM categories WHERE name='Clothing'), 'Western Wear', 'Sassafras', 1499.00, 250.00, 20, 'images/products/maxi_dress.webp', 'Floral maxi dress', 'scheduled', 4.5, 1, NULL),
('Women Denim Jacket', (SELECT id FROM categories WHERE name='Clothing'), 'Winter Wear', 'Levis', 1999.00, 300.00, 15, 'images/products/denim_jacket.jpg', 'Stylish denim jacket', 'scheduled', 4.6, 0, NULL),
('Women Palazzo Pants', (SELECT id FROM categories WHERE name='Clothing'), 'Bottom Wear', 'Global Desi', 799.00, 100.00, 30, 'images/products/palazzo.webp', 'Comfortable palazzo pants', 'scheduled', 4.3, 1, NULL),
('Women Night Suit', (SELECT id FROM categories WHERE name='Clothing'), 'Sleepwear', 'Clovia', 899.00, 120.00, 25, 'images/products/nightsuit.webp', 'Soft cotton nightwear', 'scheduled', 4.4, 1, NULL),
('Boys T-Shirt', (SELECT id FROM categories WHERE name='Clothing'), 'Kidswear', 'Gini & Jony', 399.00, 50.00, 40, 'images/products/boys_tshirt.webp', 'Printed boys t-shirt', 'scheduled', 4.2, 1, NULL),
('Girls Frock', (SELECT id FROM categories WHERE name='Clothing'), 'Kidswear', 'Hopscotch', 699.00, 100.00, 30, 'images/products/girls_frock.jpeg', 'Cute party frock', 'scheduled', 4.5, 1, NULL),
('Kids School Uniform Set', (SELECT id FROM categories WHERE name='Clothing'), 'Kidswear', 'Allen Solly Jr', 999.00, 150.00, 20, 'images/products/school_uniform.webp', 'Complete uniform set', 'scheduled', 4.4, 0, NULL),
('Baby Romper', (SELECT id FROM categories WHERE name='Clothing'), 'Kidswear', 'Mothercare', 499.00, 80.00, 35, 'images/products/romper.jpeg', 'Soft baby romper', 'scheduled', 4.6, 1, NULL);

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Shampoo 180ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Hair Care', 'Clinic Plus', 120.00, 10.00, 60, 'images/products/shampoo.jpg', 'Hair shampoo for daily use', 'instant', 4.1, 1, 25),
('Detergent Powder 1kg', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Surf Excel', 210.00, 15.00, 35, 'images/products/detergent.jpg', 'Laundry detergent powder', 'instant', 4.6, 0, 30),
('Face Wash 100ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Skin Care', 'Himalaya', 150.00, 15.00, 55, 'images/products/facewash.webp', 'Herbal face wash', 'instant', 4.2, 1, 20),
('Toothpaste 200g', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Oral Care', 'Colgate', 95.00, 10.00, 75, 'images/products/toothpaste.webp', 'Cavity protection toothpaste', 'instant', 4.5, 0, 25),
('Floor Cleaner 1L', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Lizol', 160.00, 20.00, 45, 'images/products/floorcleaner.webp', 'Disinfectant floor cleaner', 'instant', 4.4, 0, 30),
('Dishwash Liquid 500ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Vim', 110.00, 10.00, 50, 'images/products/dishwash.jpg', 'Powerful grease cleaner', 'instant', 4.3, 1, 20),
('Hair Oil 200ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Hair Care', 'Parachute', 140.00, 10.00, 60, 'images/products/hairoil.webp', 'Coconut hair oil', 'instant', 4.5, 1, 30),
('Body Soap Pack', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Bath', 'Lux', 120.00, 15.00, 70, 'images/products/soap.jpeg', 'Set of 3 soaps', 'instant', 4.3, 0, 20),
('Hand Sanitizer 100ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Hygiene', 'Dettol', 60.00, 5.00, 90, 'images/products/sanitizer.jpg', 'Kills 99.9% germs', 'instant', 4.6, 1, 15),
('Garbage Bags Pack', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'CleanPro', 90.00, 10.00, 50, 'images/products/garbage.webp', 'Disposable garbage bags', 'instant', 4.2, 0, 25),
('Aluminium Foil 25m', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Kitchen', 'FreshWrap', 110.00, 10.00, 45, 'images/products/foil.webp', 'Food wrapping foil', 'instant', 4.4, 0, 30),
('Face Cream 100ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Skin Care', 'Nivea', 220.00, 20.00, 60, 'images/products/facecream.webp', 'Moisturizing face cream', 'instant', 4.4, 1, 25),
('Body Lotion 200ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Skin Care', 'Vaseline', 280.00, 30.00, 50, 'images/products/bodylotion.jpg', 'Hydrating body lotion', 'instant', 4.5, 1, 30),
('Shaving Cream 100g', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Grooming', 'Gillette', 150.00, 10.00, 70, 'images/products/shavingcream.jpg', 'Smooth shaving cream', 'instant', 4.3, 0, 20),
('Hand Wash 500ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Hygiene', 'Lifebuoy', 180.00, 15.00, 80, 'images/products/handwash.webp', 'Kills germs effectively', 'instant', 4.5, 1, 20),
('Toilet Cleaner 500ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Harpic', 120.00, 10.00, 60, 'images/products/toiletcleaner.webp', 'Powerful toilet cleaner', 'instant', 4.4, 0, 30),
('Glass Cleaner 500ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Colin', 130.00, 15.00, 55, 'images/products/glasscleaner.webp', 'Streak-free shine cleaner', 'instant', 4.3, 0, 25),
('Liquid Detergent 1L', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Ariel', 350.00, 40.00, 40, 'images/products/liquiddetergent.webp', 'Liquid laundry detergent', 'instant', 4.6, 1, 30),
('Fabric Conditioner 500ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Cleaning', 'Comfort', 220.00, 20.00, 45, 'images/products/conditioner.jpg', 'Soft fabric conditioner', 'instant', 4.4, 1, 30),
('Mouthwash 250ml', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Oral Care', 'Listerine', 180.00, 15.00, 50, 'images/products/mouthwash.jpg', 'Fresh breath mouthwash', 'instant', 4.5, 1, 25),
('Toothbrush Pack', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Oral Care', 'Oral-B', 120.00, 10.00, 70, 'images/products/toothbrush.webp', 'Set of 2 toothbrushes', 'instant', 4.3, 0, 30),
('Baby Diapers Pack', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Baby Care', 'Pampers', 699.00, 80.00, 30, 'images/products/diapers.webp', 'Comfortable baby diapers', 'instant', 4.7, 1, 20),
('Baby Powder 200g', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Baby Care', 'Johnson', 180.00, 15.00, 40, 'images/products/babypowder.webp', 'Soft baby powder', 'instant', 4.6, 1, 30),
('Matchbox Pack', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Household', 'Home', 20.00, 0.00, 150, 'images/products/matchbox.webp', 'Pack of matchboxes', 'instant', 4.1, 0, 60),
('Mosquito Repellent Liquid', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Household', 'Good Knight', 150.00, 15.00, 50, 'images/products/repellent.webp', 'Mosquito protection liquid', 'instant', 4.4, 1, 30),
('Air Freshener Spray', (SELECT id FROM categories WHERE name='Daily Essentials'), 'Household', 'Odonil', 220.00, 20.00, 40, 'images/products/airfreshener.webp', 'Room freshener spray', 'instant', 4.3, 0, 25);

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Classmate Notebook 200 Pages', (SELECT id FROM categories WHERE name='Stationery'), 'Stationery', 'Classmate', 75.00, 10.00, 50, 'images/products/book.webp', 'Classmate long notebook', 'instant', 4.4, 1, 4);

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Pentonic Ball point pens',(SELECT id FROM categories WHERE name='Stationery'),'Stationery','Pentonic',100.00,20.00,50,'images/products/pens.webp','Pentonic (Blue,Black,Red) pens','instant',4.2,1,2);

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Doms wax crayons',(SELECT id FROM categories WHERE name='Stationery'),'Stationery','Doms',20.00,0.00,50,'images/products/crayons.jpg','Doms crayon set of 12 shades','instant',4.2,1,2),
('Classmate geometry box',(SELECT id FROM categories WHERE name='Stationery'),'Stationery','Classmate Victor',120.00,20.00,50,'images/products/geometrybox.webp','Classmate Geo box ','instant',4.5,1,2),
('JK Easy Copier',(SELECT id FROM categories WHERE name='Stationery'),'Stationery','JK',200.00,0.00,50,'images/products/a4sheets.webp','A4 sheets 75gsm','instant',4.2,1,5),
('Apsara Scholar Kit',(SELECT id FROM categories WHERE name='Stationery'),'Stationery','Apsara',180.00,20.00,50,'images/products/penskit.jpeg','Complete Stationery Gift Set With Pencils, Eraser, Sharpener & Scale ','instant',4.2,1,2);

INSERT INTO products
(name, category_id, subcategory, brand, price, discount, stock, image, description, delivery_type, rating, is_student_pick, refill_days)
VALUES
('Qunyou SchoolBag',(SELECT id FROM  categories WHERE name ='Stationery'),'Stationery','Qunyou',700.00,50.00,10,'images/products/schoolbag.jpeg','School Bag','scheduled',4.3,1,5),
('Flair Penholder',(SELECT id FROM  categories WHERE name ='Stationery'),'Stationery','Flair',80.00,0.00,20,'images/products/penholder.webp','Multipurpose desktop penholder','instant',4.0,1,10);
SELECT MAX(id) FROM products;
ALTER TABLE products AUTO_INCREMENT = 59;


ALTER TABLE products ADD product_code varchar(20) UNIQUE;

ALTER TABLE orders ADD COLUMN order_number varchar(20)  UNIQUE;

UPDATE products SET product_code = CONCAT('PRD', LPAD(id,3,'0')) where product_code is NULL;
UPDATE orders SET order_number = CONCAT('ORD', LPAD(id,4,'0')) where order_number is NULL;

UPDATE users SET is_admin = 1 WHERE email = 'sadvi@gmail.com';