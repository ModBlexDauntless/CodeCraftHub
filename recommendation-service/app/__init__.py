from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config

# Initialize extensions **outside** create_app() to avoid circular imports
mongo = PyMongo()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app, origins=["http://localhost:3000"])

    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)

    # Import blueprints inside the function to avoid circular imports
    from app.routes.recommendations import recommendation_bp
    app.register_blueprint(recommendation_bp)

    # Health check
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok"}), 200

    return app
