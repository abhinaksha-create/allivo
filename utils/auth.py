from flask import session, flash, redirect, url_for

def login_required():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))
    return None

def admin_required():
    if "user_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    if not session.get("is_admin"):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("home"))

    return None