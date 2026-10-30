import os
import sqlite3
from app.admin import admin_bp
from flask import Flask, jsonify, request, render_template
from app.cart import validate_menu_dish
from app.integration import load_menu
from app.recommendations import recommend
from app.validation import build_guest_context, validate_guest_json


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("RSHB_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("RSHB_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=900,
    )

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error):
        app.logger.error(
            "Database operation failed: %s",
            type(error).__name__,
        )

        message = "Меню временно недоступно. Повторите позже."

        if request.path.startswith("/api/"):
            return jsonify({"error": message}), 503

        return message, 503

    @app.route("/")
    def index():
        return "It works"

    @app.get("/menu")
    def guest_menu():
        db_path = app.config.get("ADMIN_DB_PATH")
        try:
            menu = load_menu(1, db_path=db_path)
        except (ValueError, OSError):
            return "Menu not available", 503

        dishes = [
            dish for dish in menu.dishes if dish.available
        ]

        return render_template("menu.html", dishes=dishes)

    @app.post("/api/recommendations")
    def get_recommendations():
        data = request.get_json(silent=True)

        try:
            validate_guest_json(data)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        db_path = app.config.get("ADMIN_DB_PATH")
        try:
            menu = load_menu(1, db_path=db_path)
        except (ValueError, OSError) as error:
            app.logger.error("Menu loading failed: %s", type(error).__name__)
            return jsonify({"error": "Menu temporarily unavailable"}), 503

        try:
            guest = build_guest_context(data, menu, restaurant_id=1)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        results = recommend(menu, guest)

        return jsonify([
            {
                "dish_id": item.dish_id,
                "name": item.name,
                "price_kopeck": item.price_kopeck,
                "score": item.score,
                "reasons": item.reasons,
            }
            for item in results
        ])

    @app.post("/api/cart/validate")
    def validate_cart_addition():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Expected JSON object"}), 400

        dish_id = data.get("dish_id")

        if type(dish_id) is not int or dish_id <= 0:
            return jsonify({"error": "Invalid dish_id"}), 400

        try:
            validate_guest_json(data)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        db_path = app.config.get("ADMIN_DB_PATH")
        try:
            menu = load_menu(1, db_path=db_path)
        except (ValueError, OSError):
            return jsonify({"error": "Menu temporarily unavailable"}), 503

        try:
            guest = build_guest_context(data, menu, restaurant_id=1)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        dish = next(
            (item for item in menu.dishes if item.id == dish_id and item.restaurant_id == 1),
            None,
        )

        if dish is None:
            return jsonify({"error": "Dish not found"}), 404

        if not dish.available:
            return jsonify({"error": "Dish unavailable"}), 409

        if dish_id in guest.cart_dish_ids:
            return jsonify({"error": "Dish already in cart"}), 409

        allowed = recommend(menu, guest)

        if not any(item.dish_id == dish_id for item in allowed):
            return jsonify({"error": "Dish not permitted for current recommendations"}), 409

        return jsonify({
            "dish_id": dish.id,
            "name": dish.name,
            "price_kopeck": dish.price_kopeck,
            "validated": True,
        })


    @app.post("/api/menu/add/validate")
    def validate_menu_addition():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Expected JSON object"}), 400

        dish_id = data.get("dish_id")

        if type(dish_id) is not int or dish_id <= 0:
            return jsonify({"error": "Invalid dish_id"}), 400

        try:
            validate_guest_json(data)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        db_path = app.config.get("ADMIN_DB_PATH")
        try:
            menu = load_menu(1, db_path=db_path)
        except (ValueError, OSError):
            return jsonify({"error": "Menu temporarily unavailable"}), 503

        try:
            guest = build_guest_context(data, menu, restaurant_id=1)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        try:
            dish = validate_menu_dish(menu, guest, dish_id)
        except ValueError as error:
            return jsonify({"error": str(error)}), 409

        return jsonify({
            "validated": True,
            "dish_id": dish.id,
            "name": dish.name,
            "price_kopeck": dish.price_kopeck,
            "category": dish.category
        })

    app.register_blueprint(admin_bp)

    return app
