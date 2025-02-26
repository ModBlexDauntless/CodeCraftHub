from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from app.config import Config
import os

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)
    
    # Ensure the upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints (routes)
    from app.routes.exercises import exercises_bp
    
    app.register_blueprint(exercises_bp)
    
    # Add a simple health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        from flask import jsonify
        return jsonify({"status": "ok"}), 200
    
    return app