from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models.user import create_user_document

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if user already exists
    existing_user = mongo.db.users.find_one({
        '$or': [
            {'username': data['username']},
            {'email': data['email']}
        ]
    })
    
    if existing_user:
        return jsonify({"message": "Username or email already exists"}), 400
    
    # Create new user with hashed password
    hashed_password = generate_password_hash(data['password'])
    
    # Prepare user document
    new_user = create_user_document(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        learning_style=data.get('learning_style', 'visual'),
        difficulty_preference=data.get('difficulty_preference', 'beginner'),
        interests=data.get('interests', [])
    )
    
    # Insert into database
    result = mongo.db.users.insert_one(new_user)
    
    return jsonify({
        "message": "User created successfully",
        "user_id": str(result.inserted_id)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    
    # Find user by username
    user = mongo.db.users.find_one({'username': data['username']})
    
    # Check if user exists and password is correct
    if user and check_password_hash(user['password'], data['password']):
        # Create access token
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({"access_token": access_token}), 200
    
    return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    # Get user ID from the JWT token
    current_user_id = get_jwt_identity()
    
    # Find user in database
    from bson.objectid import ObjectId
    user = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Convert ObjectId to string for JSON serialization
    user['_id'] = str(user['_id'])
    
    # Return user profile data (excluding password)
    user.pop('password', None)
    
    return jsonify(user), 200