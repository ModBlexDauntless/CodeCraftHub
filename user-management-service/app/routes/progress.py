# File: app/routes/progress.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from datetime import datetime
from app.models.progress import create_progress_document, create_content_progress

progress_bp = Blueprint('progress', __name__, url_prefix='/api/progress')

@progress_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_user_progress():
    # Get current user ID from the JWT token
    current_user_id = get_jwt_identity()
    
    # Get all progress records for this user
    progress_records = list(mongo.db.progress.find({'user_id': ObjectId(current_user_id)}))
    
    # Format the response
    result = []
    for progress in progress_records:
        # Get course title
        course = mongo.db.courses.find_one({'_id': progress['course_id']}, {'title': 1})
        
        if course:
            result.append({
                "course_id": str(progress['course_id']),
                "course_title": course['title'],
                "progress_percentage": progress['progress_percentage'],
                "last_accessed": progress['last_accessed'].isoformat(),
                "completed": progress['completed'],
                "time_spent": progress['time_spent']
            })
    
    return jsonify(result), 200

@progress_bp.route('/courses/<course_id>', methods=['POST'])
@jwt_required()
def update_course_progress(course_id):
    # Get current user ID from the JWT token
    current_user_id = get_jwt_identity()
    
    # Check if the course exists
    course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
    if not course:
        return jsonify({"message": "Course not found"}), 404
    
    # Check if a progress record already exists
    progress = mongo.db.progress.find_one({
        'user_id': ObjectId(current_user_id),
        'course_id': ObjectId(course_id)
    })
    
    # If no record exists, create a new one
    if not progress:
        progress_doc = create_progress_document(current_user_id, course_id)
        mongo.db.progress.insert_one(progress_doc)
        progress = progress_doc
    
    # Update progress data
    data = request.json
    update_fields = {}
    
    if 'progress_percentage' in data:
        update_fields['progress_percentage'] = data['progress_percentage']
    if 'completed' in data:
        update_fields['completed'] = data['completed']
    if 'time_spent' in data:
        # Add the new time to the existing time spent
        update_fields['time_spent'] = progress.get('time_spent', 0) + data['time_spent']
    
    # Update last accessed timestamp
    update_fields['last_accessed'] = datetime.utcnow()
    
    # Save changes
    mongo.db.progress.update_one(
        {
            'user_id': ObjectId(current_user_id),
            'course_id': ObjectId(course_id)
        },
        {'$set': update_fields}
    )
    
    return jsonify({"message": "Progress updated successfully"}), 200

@progress_bp.route('/content/<course_id>/<module_index>/<content_index>', methods=['POST'])
@jwt_required()
def update_content_progress(course_id, module_index, content_index):
    # Get current user ID from the JWT token
    current_user_id = get_jwt_identity()
    
    # Check if the course and content exist
    course = mongo.db.courses.find_one(
        {'_id': ObjectId(course_id)},
        {'modules': {'$elemMatch': {'order': int(module_index)}}}
    )
    
    if not course or 'modules' not in course or not course['modules']:
        return jsonify({"message": "Module not found"}), 404
    
    module = course['modules'][0]
    
    # Create a unique ID for this content item
    content_id = f"{module_index}:{content_index}"
    
    # Check if a progress record already exists for this course
    progress = mongo.db.progress.find_one({
        'user_id': ObjectId(current_user_id),
        'course_id': ObjectId(course_id)
    })
    
    # If no record exists, create a new one
    if not progress:
        progress_doc = create_progress_document(current_user_id, course_id)
        mongo.db.progress.insert_one(progress_doc)
        progress_id = progress_doc['_id']
    else:
        progress_id = progress['_id']
    
    # Data to update
    data = request.json
    
    # Check if content progress entry already exists
    content_exists = mongo.db.progress.find_one({
        '_id': progress_id,
        'content_progress.content_id': content_id
    })
    
    if content_exists:
        # Update existing content progress
        update_fields = {}
        
        if 'viewed' in data:
            update_fields['content_progress.$.viewed'] = data['viewed']
        if 'completed' in data:
            update_fields['content_progress.$.completed'] = data['completed']
        if 'time_spent' in data:
            # Find current time spent
            for cp in content_exists.get('content_progress', []):
                if cp['content_id'] == content_id:
                    current_time = cp.get('time_spent', 0)
                    break
            else:
                current_time = 0
                
            update_fields['content_progress.$.time_spent'] = current_time + data['time_spent']
        
        update_fields['content_progress.$.last_accessed'] = datetime.utcnow()
        
        mongo.db.progress.update_one(
            {
                '_id': progress_id,
                'content_progress.content_id': content_id
            },
            {'$set': update_fields}
        )
    else:
        # Add new content progress entry
        content_progress = create_content_progress(content_id)
        
        if 'viewed' in data:
            content_progress['viewed'] = data['viewed']
        if 'completed' in data:
            content_progress['completed'] = data['completed']
        if 'time_spent' in data:
            content_progress['time_spent'] = data['time_spent']
        
        mongo.db.progress.update_one(
            {'_id': progress_id},
            {'$push': {'content_progress': content_progress}}
        )
    
    # Calculate overall progress percentage
    # Count the total number of content items in this course
    course_full = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
    total_content_items = 0
    
    for module in course_full.get('modules', []):
        total_content_items += len(module.get('content_items', []))
    
    # Get the updated progress document
    updated_progress = mongo.db.progress.find_one({'_id': progress_id})
    
    # Count completed content items
    completed_items = sum(1 for cp in updated_progress.get('content_progress', []) 
                         if cp.get('completed', False))
    
    # Calculate and update overall progress
    if total_content_items > 0:
        progress_percentage = (completed_items / total_content_items) * 100
        
        # Update the overall course progress
        mongo.db.progress.update_one(
            {'_id': progress_id},
            {
                '$set': {
                    'progress_percentage': progress_percentage,
                    'last_accessed': datetime.utcnow(),
                    'completed': progress_percentage >= 100
                }
            }
        )
    
    return jsonify({"message": "Content progress updated successfully"}), 200