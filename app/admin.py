import os
import secrets
from pathlib import Path
from app.admin_data import set_dish_availability, set_dish_price, update_restaurant_rules

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
    current_app
)
from werkzeug.security import check_password_hash


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if not os.environ.get("RSHB_SECRET_KEY"):
        abort(503)

    username = os.environ.get("RSHB_ADMIN_USER")
    password_hash = os.environ.get("RSHB_ADMIN_PASSWORD_HASH")

    if not username or not password_hash:
        abort(503)

    if request.method == "GET":
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
        return render_template("admin_login.html", csrf_token=token)

    submitted_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")

    if not expected_token or not secrets.compare_digest(
        submitted_token, expected_token
    ):
        abort(400)

    submitted_username = request.form.get("username", "")
    submitted_password = request.form.get("password", "")

    if (
        secrets.compare_digest(submitted_username, username)
        and check_password_hash(password_hash, submitted_password)
    ):
        session.clear()
        session["admin_authenticated"] = True
        session["csrf_token"] = secrets.token_urlsafe(32)
        session.permanent = True
        return redirect(url_for("admin.dashboard"))

    abort(401)


@admin_bp.get("/")
def dashboard():
    if not session.get("admin_authenticated"):
        return redirect(url_for("admin.login"))

    from app.integration import load_menu

    try:
        menu = load_menu(1)

    except (ValueError, OSError):
        abort(503)

    return render_template(
        "admin_dashboard.html",
        dishes = menu.dishes,
        rules = menu,
        csrf_token = session["csrf_token"],
    )

@admin_bp.post("/logout")
def logout():
    if not session.get("admin_authenticated"):
        abort(403)

    submitted_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")

    if not expected_token or not secrets.compare_digest(
        submitted_token, expected_token
    ):
        abort(400)

    session.clear()
    return redirect(url_for("admin.login"))

@admin_bp.post("/dishes/<int:dish_id>/availability")
def change_dish_availability(dish_id):
    if not session.get("admin_authenticated"):
        abort(403)

    submitted_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")

    if not expected_token or not secrets.compare_digest(submitted_token, expected_token):
        abort(400)

    value = request.form.get("available")

    if value not in ("0", "1"):
        abort(400)

    db_path = current_app.config.get(
    "ADMIN_DB_PATH",
    Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db",
)

    try:
        set_dish_availability(db_path, restaurant_id = 1, dish_id = dish_id, available = value == "1")
    except ValueError:
        abort(404)

    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/dishes/<int:dish_id>/price")
def change_dish_price(dish_id):
    if not session.get("admin_authenticated"):
        abort(403)

    submitted_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")

    if not expected_token or not secrets.compare_digest(
        submitted_token, expected_token
    ):
        abort(400)

    price_text = request.form.get("price_kopeck", "")

    if not price_text.isascii() or not price_text.isdecimal():
        abort(400)

    price_kopeck = int(price_text)

    if price_kopeck <= 0 or price_kopeck > 100000000:
        abort(400)

    db_path = current_app.config.get(
        "ADMIN_DB_PATH",
        Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db",
    )

    try:
        set_dish_price(
            db_path,
            restaurant_id = 1,
            dish_id = dish_id,
            price_kopeck = price_kopeck,
        )
    except ValueError:
        abort(404)

    return redirect(url_for("admin.dashboard"))

@admin_bp.post("/rules")
def change_restaurant_rules():
    if not session.get("admin_authenticated"):
        abort(403)

    submitted_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")

    if not expected_token or not secrets.compare_digest(
        submitted_token, expected_token
    ):
        abort(400)

    weight_names = (
        "preference_weight",
        "pairing_weight",
        "category_weight",
    )

    weights = {}

    for name in weight_names:
        value = request.form.get(name, "")

        if len(value) != 1 or value not in "012345":
            abort(400)

        weights[name] = int(value)

    enabled_value = request.form.get("enabled", "0")

    if enabled_value not in ("0", "1"):
        abort(400)

    db_path = current_app.config.get(
        "ADMIN_DB_PATH",
        Path(__file__).resolve().parent.parent / "instance" / "rshb_chef.db",
    )

    try:
        update_restaurant_rules(
            db_path,
            restaurant_id = 1,
            preference_weight = weights["preference_weight"],
            pairing_weight = weights["pairing_weight"],
            category_weight = weights["category_weight"],
            enabled=enabled_value == "1",
        )
    except ValueError:
        abort(404)

    return redirect(url_for("admin.dashboard"))
