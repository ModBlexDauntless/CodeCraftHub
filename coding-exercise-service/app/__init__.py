from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config
import os

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for all routes
    CORS(app, origins=["http://localhost:3000"])

    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)

    # Ensure the upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    # Import blueprints inside the function to avoid circular imports
    from app.routes.exercises import exercises_bp
    app.register_blueprint(exercises_bp)

    # Health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok"}), 200

    return app
