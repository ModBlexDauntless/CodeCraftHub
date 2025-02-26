from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from app.config import Config

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)
    
    # Register blueprints (routes)
    from app.routes.recommendations import recommendation_bp
    
    app.register_blueprint(recommendation_bp)
    
    # Add a simple health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        from flask import jsonify
        return jsonify({"status": "ok"}), 200
    
    return app