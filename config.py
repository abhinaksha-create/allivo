import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "my_secret_key_123")
    ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "Abhistore@2026#Admin")

    DB_TYPE = os.environ.get("DB_TYPE", "sqlite")
    SQLITE_DB = os.environ.get("SQLITE_DB", os.path.join(BASE_DIR, "site.db"))

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "allivo.notifications@gmail.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "uvncgbsbvzookatd")
    MAIL_DEFAULT_SENDER = ("Allivo", os.environ.get("MAIL_USERNAME", "allivo.notifications@gmail.com"))