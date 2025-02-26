from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from bson.objectid import ObjectId
from datetime import datetime
from app.models.exercise import create_exercise_document
from app.services.code_execution import CodeExecutionService

exercises_bp = Blueprint('exercises', __name__, url_prefix='/api/exercises')
code_executor = CodeExecutionService()

@exercises_bp.route('/', methods=['GET'])
@jwt_required()
def get_exercises():
    # Get query parameters for filtering
    topic = request.args.get('topic')
    difficulty = request.args.get('difficulty')
    
    # Build query
    query = {}
    if topic:
        query['topic'] = topic
    if difficulty:
        query['difficulty'] = difficulty
    
    # Get exercises
    exercises = list(mongo.db.exercises.find(
        query,
        {
            'title': 1,
            'description': 1,
            'difficulty': 1,
            'topic': 1,
            'test_cases': {'$slice': 0}  # Don't include test cases
        }
    ))
    
    # Convert ObjectIds to strings
    for exercise in exercises:
        exercise['_id'] = str(exercise['_id'])
    
    return jsonify(exercises), 200

@exercises_bp.route('/<exercise_id>', methods=['GET'])
@jwt_required()
def get_exercise(exercise_id):
    try:
        # Project non-hidden test cases
        pipeline = [
            {'$match': {'_id': ObjectId(exercise_id)}},
            {'$project': {
                'solution_code': 0,  # Don't include solution code
                'test_cases': {
                    '$filter': {
                        'input': '$test_cases',
                        'as': 'test_case',
                        'cond': {'$eq': ['$$test_case.is_hidden', False]}
                    }
                }
            }}
        ]
        
        exercise_cursor = mongo.db.exercises.aggregate(pipeline)
        exercise = next(exercise_cursor, None)
        
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404
        
        # Convert ObjectId to string
        exercise['_id'] = str(exercise['_id'])
        
        return jsonify(exercise), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@exercises_bp.route('/<exercise_id>/hints', methods=['GET'])
@jwt_required()
def get_hints(exercise_id):
    try:
        # Get requested hint level
        level = int(request.args.get('level', 1))
        
        # Get exercise hints
        exercise = mongo.db.exercises.find_one(
            {'_id': ObjectId(exercise_id)},
            {'hints': 1}
        )
        
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404
        
        # Filter hints by level
        hints = [hint for hint in exercise.get('hints', []) if hint['level'] <= level]
        
        return jsonify({"hints": hints}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@exercises_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_code():
    data = request.json
    
    # Validate required fields
    if not all(k in data for k in ('exercise_id', 'language', 'code')):
        return jsonify({"message": "Missing required fields"}), 400
    
    try:
        # Get exercise
        exercise = mongo.db.exercises.find_one({'_id': ObjectId(data['exercise_id'])})
        if not exercise:
            return jsonify({"message": "Exercise not found"}), 404
        
        # Process submissions based on language
        if data['language'].lower() == 'python':
            results = []
            for i, test_case in enumerate(exercise['test_cases']):
                result = code_executor.execute_python(data['code'], test_case['input'])
                
                # Check result
                if result['success']:
                    passed = result['output'] == test_case['expected_output']
                    results.append({
                        "test_case_id": i,
                        "passed": passed,
                        "expected": test_case['expected_output'],
                        "actual": result['output'],
                        "hidden": test_case.get('is_hidden', False)
                    })
                else:
                    results.append({
                        "test_case_id": i,
                        "passed": False,
                        "error": result['error'],
                        "hidden": test_case.get('is_hidden', False)
                    })
        else:
            # Handle other languages
            return jsonify({"message": f"Language {data['language']} not supported yet"}), 400
        
        # Save submission
        user_id = get_jwt_identity()
        submission = {
            "user_id": ObjectId(user_id),
            "exercise_id": ObjectId(data['exercise_id']),
            "language": data['language'],
            "code": data['code'],
            "results": results,
            "submitted_at": datetime.utcnow(),
            "passed_all": all(r['passed'] for r in results)
        }
        
        mongo.db.submissions.insert_one(submission)
        
        # For the response, remove hidden test case details
        visible_results = [r for r in results if not r.get('hidden', False)]
        
        return jsonify({
            "results": visible_results,
            "passed_all": all(r['passed'] for r in results),
            "passed_visible": all(r['passed'] for r in visible_results)
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@exercises_bp.route('/', methods=['POST'])
@jwt_required()
def create_exercise():
    data = request.json
    
    # Validate required fields
    required_fields = ['title', 'description', 'difficulty', 'topic']
    if not all(field in data for field in required_fields):
        return jsonify({"message": f"Missing required fields: {', '.join(required_fields)}"}), 400
    
    # Create new exercise document
    new_exercise = create_exercise_document(
        title=data['title'],
        description=data['description'],
        difficulty=data['difficulty'],
        topic=data['topic'],
        test_cases=data.get('test_cases', []),
        starter_code=data.get('starter_code', {}),
        solution_code=data.get('solution_code', {}),
        hints=data.get('hints', [])
    )
    
    # Insert into database
    result = mongo.db.exercises.insert_one(new_exercise)
    
    return jsonify({
        "message": "Exercise created successfully",
        "exercise_id": str(result.inserted_id)
    }), 201