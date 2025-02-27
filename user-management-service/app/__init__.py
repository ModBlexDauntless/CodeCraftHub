# File: app/__init__.py
from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app)
    
    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)
    
    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    
    app.register_blueprint(auth_bp)
    
    return app