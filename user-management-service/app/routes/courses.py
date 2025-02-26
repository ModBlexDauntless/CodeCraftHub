# File: app/routes/courses.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from app.models.course import create_course_document, create_module_document, create_content_item_document
import os
from werkzeug.utils import secure_filename

courses_bp = Blueprint('courses', __name__, url_prefix='/api/courses')

@courses_bp.route('/', methods=['GET'])
@jwt_required()
def get_courses():
    # Get all courses (in a real app, you'd add pagination)
    courses = list(mongo.db.courses.find({}, {
        'title': 1,
        'description': 1,
        'difficulty': 1,
        'category': 1,
        'estimated_duration': 1,
        'modules': {'$slice': 0}  # Don't retrieve modules array
    }))
    
    # Add module count to each course
    for course in courses:
        course['_id'] = str(course['_id'])
        
        # Count modules by querying the modules array length
        course_with_modules = mongo.db.courses.find_one(
            {'_id': ObjectId(course['_id'])},
            {'modules': 1}
        )
        course['modules_count'] = len(course_with_modules.get('modules', []))
    
    # Convert MongoDB documents to JSON
    return json.loads(dumps(courses)), 200

@courses_bp.route('/<course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    try:
        # Get specific course with detailed information
        course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
        
        if not course:
            return jsonify({"message": "Course not found"}), 404
        
        # Convert ObjectId to string for JSON serialization
        course['_id'] = str(course['_id'])
        
        # Convert MongoDB document to JSON
        return json.loads(dumps(course)), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@courses_bp.route('/<course_id>/modules/<int:module_index>', methods=['GET'])
@jwt_required()
def get_module_content(course_id, module_index):
    try:
        # Get the course
        course = mongo.db.courses.find_one(
            {'_id': ObjectId(course_id)},
            {'modules': {'$elemMatch': {'order': module_index}}}
        )
        
        if not course or 'modules' not in course or not course['modules']:
            return jsonify({"message": "Module not found"}), 404
        
        module = course['modules'][0]  # We used $elemMatch so there's only one
        
        # Convert MongoDB document to JSON
        return json.loads(dumps(module)), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@courses_bp.route('/', methods=['POST'])
@jwt_required()
def create_course():
    data = request.json
    
    # Create new course document
    new_course = create_course_document(
        title=data['title'],
        description=data['description'],
        difficulty=data['difficulty'],
        category=data['category'],
        tags=data.get('tags', []),
        estimated_duration=data.get('estimated_duration', 0)
    )
    
    # Insert into database
    result = mongo.db.courses.insert_one(new_course)
    
    return jsonify({
        "message": "Course created successfully",
        "course_id": str(result.inserted_id)
    }), 201

@courses_bp.route('/<course_id>/modules', methods=['POST'])
@jwt_required()
def add_module(course_id):
    data = request.json
    
    # Create new module document
    new_module = create_module_document(
        title=data['title'],
        description=data['description'],
        order=data['order']
    )
    
    # Add module to course
    result = mongo.db.courses.update_one(
        {'_id': ObjectId(course_id)},
        {'$push': {'modules': new_module}}
    )
    
    if result.modified_count == 0:
        return jsonify({"message": "Course not found or module not added"}), 404
    
    return jsonify({"message": "Module added successfully"}), 200

@courses_bp.route('/<course_id>/modules/<int:module_index>/content', methods=['POST'])
@jwt_required()
def add_content(course_id, module_index):
    data = request.json
    
    # Create new content item document
    new_content = create_content_item_document(
        title=data['title'],
        content_type=data['content_type'],
        content_url=data['content_url'],
        order=data['order'],
        difficulty=data.get('difficulty'),
        learning_style=data.get('learning_style'),
        estimated_time=data.get('estimated_time', 0)
    )
    
    # Add content item to module
    result = mongo.db.courses.update_one(
        {
            '_id': ObjectId(course_id),
            'modules.order': module_index
        },
        {'$push': {'modules.$.content_items': new_content}}
    )
    
    if result.modified_count == 0:
        return jsonify({"message": "Course or module not found"}), 404
    
    return jsonify({"message": "Content item added successfully"}), 200