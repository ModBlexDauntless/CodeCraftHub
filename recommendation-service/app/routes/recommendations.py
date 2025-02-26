from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from bson.objectid import ObjectId
from app.services.recommendation_engine import RecommendationEngine

recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

@recommendation_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_course_recommendations():
    user_id = get_jwt_identity()
    
    # Get query parameters
    limit = int(request.args.get('limit', 5))
    
    # Get recommendations
    recommendations = recommendation_engine.recommend_courses_for_user(user_id, limit)
    
    return jsonify({"recommendations": recommendations}), 200

@recommendation_bp.route('/exercises', methods=['GET'])
@jwt_required()
def get_exercise_recommendations():
    user_id = get_jwt_identity()
    
    # Get query parameters
    limit = int(request.args.get('limit', 5))
    
    # Get recommendations
    recommendations = recommendation_engine.recommend_exercises_for_user(user_id, limit)
    
    # Format recommendations for the response
    formatted_recommendations = []
    for rec in recommendations:
        # Remove potentially large fields
        rec.pop('solution_code', None)
        rec.pop('test_cases', None)
        formatted_recommendations.append(rec)
    
    return jsonify({"recommendations": formatted_recommendations}), 200

@recommendation_bp.route('/learning-path', methods=['POST'])
@jwt_required()
def generate_learning_path():
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate input
    if 'goal' not in data:
        return jsonify({"message": "Missing learning goal"}), 400
    
    # Generate learning path
    learning_path = recommendation_engine.generate_learning_path(
        user_id, 
        data['goal'], 
        data.get('timeframe', 'medium')  # short, medium, long
    )
    
    return jsonify({"learning_path": learning_path}), 200

@recommendation_bp.route('/learning-paths', methods=['GET'])
@jwt_required()
def get_learning_paths():
    user_id = get_jwt_identity()
    
    # Get all learning paths for this user
    learning_paths = list(mongo.db.learning_paths.find({'user_id': user_id}))
    
    # Convert ObjectIds to strings
    for path in learning_paths:
        path['_id'] = str(path['_id'])
    
    return jsonify({"learning_paths": learning_paths}), 200

@recommendation_bp.route('/learning-paths/<path_id>', methods=['GET'])
@jwt_required()
def get_learning_path(path_id):
    user_id = get_jwt_identity()
    
    # Get the specific learning path
    learning_path = mongo.db.learning_paths.find_one({
        '_id': ObjectId(path_id),
        'user_id': user_id
    })
    
    if not learning_path:
        return jsonify({"message": "Learning path not found"}), 404
    
    # Convert ObjectId to string
    learning_path['_id'] = str(learning_path['_id'])
    
    # Fetch details for each item in the learning path
    for item in learning_path['items']:
        if item['item_type'] == 'course':
            course = mongo.db.courses.find_one({'_id': ObjectId(item['item_id'])})
            if course:
                item['details'] = {
                    'title': course.get('title'),
                    'description': course.get('description'),
                    'difficulty': course.get('difficulty')
                }
        elif item['item_type'] == 'exercise':
            exercise = mongo.db.exercises.find_one({'_id': ObjectId(item['item_id'])})
            if exercise:
                item['details'] = {
                    'title': exercise.get('title'),
                    'description': exercise.get('description'),
                    'difficulty': exercise.get('difficulty')
                }
    
    return jsonify({"learning_path": learning_path}), 200

@recommendation_bp.route('/learning-paths/<path_id>/items/<item_index>/complete', methods=['POST'])
@jwt_required()
def mark_learning_path_item_complete(path_id, item_index):
    user_id = get_jwt_identity()
    item_index = int(item_index)
    
    # Update the item's completion status
    result = mongo.db.learning_paths.update_one(
        {
            '_id': ObjectId(path_id),
            'user_id': user_id,
            'items.order': item_index
        },
        {'$set': {'items.$.completed': True}}
    )
    
    if result.modified_count == 0:
        return jsonify({"message": "Learning path item not found or already completed"}), 404
    
    return jsonify({"message": "Learning path item marked as completed"}), 200