
from flask import Flask, jsonify, request

from app.integration import load_menu
from app.recommendations import recommend
from app.validation import build_guest_context, validate_guest_json


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "It works"

    @app.post("/api/recommendations")
    def get_recommendations():
        data = request.get_json(silent=True)

        try:
            validate_guest_json(data)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        try:
            menu = load_menu(1)
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

    return app
