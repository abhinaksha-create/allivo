import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("site.db")
cur = conn.cursor()

email = "abhinakshavarma@gmail.com"
new_password = "Admin@123"

hashed_password = generate_password_hash(new_password)

cur.execute("""
UPDATE users
SET is_admin = 1, password = ?
WHERE email = ?
""", (hashed_password, email))

conn.commit()
conn.close()

print("Admin updated successfully")
print("Email:", email)
print("Password:", new_password)