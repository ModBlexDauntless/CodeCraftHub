from app import mongo
from bson.objectid import ObjectId
import numpy as np
from datetime import datetime

class RecommendationEngine:
    def recommend_courses_for_user(self, user_id, limit=5):
        """
        Recommends courses based on user preferences and behavior.
        
        Args:
            user_id: The ID of the user to make recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended course objects
        """
        # Get user
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return []
        
        # Get user preferences
        learning_style = user.get('learning_style')
        difficulty_preference = user.get('difficulty_preference')
        interests = user.get('interests', [])
        
        # Get courses the user has already interacted with
        completed_courses = list(mongo.db.progress.find(
            {
                'user_id': ObjectId(user_id),
                'completed': True
            },
            {'course_id': 1}
        ))
        
        completed_course_ids = [str(p['course_id']) for p in completed_courses]
        
        in_progress_courses = list(mongo.db.progress.find(
            {
                'user_id': ObjectId(user_id),
                'completed': False
            },
            {'course_id': 1}
        ))
        
        in_progress_course_ids = [str(p['course_id']) for p in in_progress_courses]
        
        # Find courses that match user preferences
        # We exclude courses the user has already completed
        query = {'_id': {'$nin': [ObjectId(cid) for cid in completed_course_ids]}}
        
        # Apply filters based on preferences
        if difficulty_preference:
            query['difficulty'] = difficulty_preference
        
        # Get all potential courses
        potential_courses = list(mongo.db.courses.find(query))
        
        # Score each course based on relevance to user
        scored_courses = []
        for course in potential_courses:
            score = 0
            
            # Base score
            score += 0.5
            
            # Boost score if course matches learning style
            if learning_style and 'modules' in course:
                for module in course.get('modules', []):
                    for item in module.get('content_items', []):
                        if item.get('learning_style') == learning_style:
                            score += 0.5
            
            # Boost score if course category or tags match interests
            if interests:
                for interest in interests:
                    # Match against category
                    if course.get('category') and interest.lower() in course.get('category', '').lower():
                        score += 1
                    
                    # Match against tags
                    if course.get('tags'):
                        tags = course.get('tags', [])
                        if not isinstance(tags, list):
                            # Handle the case where tags might be a string
                            tags = tags.split(',') if isinstance(tags, str) else []
                            
                        if interest.lower() in [tag.lower() for tag in tags]:
                            score += 1
            
            # Penalize score for courses already in progress
            if str(course['_id']) in in_progress_course_ids:
                score *= 0.7
            
            # Store the scored course
            course_copy = dict(course)
            course_copy['_id'] = str(course_copy['_id'])
            course_copy['score'] = score
            scored_courses.append(course_copy)
        
        # Sort by score and get top recommendations
        scored_courses.sort(key=lambda x: x['score'], reverse=True)
        return scored_courses[:limit]
    
    def recommend_exercises_for_user(self, user_id, limit=5):
        """
        Recommends coding exercises based on user preferences and past performance.
        
        Args:
            user_id: The ID of the user to make recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended exercise objects
        """
        # Get user
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return []
        
        # Get exercises the user has already completed
        completed_submissions = list(mongo.db.submissions.find(
            {
                'user_id': ObjectId(user_id),
                'passed_all': True
            },
            {'exercise_id': 1}
        ))
        
        completed_exercise_ids = [str(s['exercise_id']) for s in completed_submissions]
        
        # Find exercises that match user preferences
        # We exclude exercises the user has already completed
        query = {'_id': {'$nin': [ObjectId(eid) for eid in completed_exercise_ids]}}
        
        # Apply filters based on preferences
        difficulty_preference = user.get('difficulty_preference')
        if difficulty_preference:
            query['difficulty'] = difficulty_preference
        
        # Get all potential exercises
        potential_exercises = list(mongo.db.exercises.find(query))
        
        # Score each exercise based on relevance to user
        scored_exercises = []
        for exercise in potential_exercises:
            score = 0
            
            # Base score
            score += 0.5
            
            # Boost score for matching topics with user interests
            interests = user.get('interests', [])
            if interests and exercise.get('topic'):
                if any(interest.lower() in exercise.get('topic', '').lower() for interest in interests):
                    score += 1
            
            # Store the scored exercise
            exercise_copy = dict(exercise)
            exercise_copy['_id'] = str(exercise_copy['_id'])
            exercise_copy['score'] = score
            scored_exercises.append(exercise_copy)
        
        # Sort by score and get top recommendations
        scored_exercises.sort(key=lambda x: x['score'], reverse=True)
        return scored_exercises[:limit]
    
    def generate_learning_path(self, user_id, goal, timeframe='medium'):
        """
        Generates a personalized learning path for a user.
        
        Args:
            user_id: The ID of the user
            goal: The learning goal (e.g., 'web development', 'data science')
            timeframe: 'short', 'medium', or 'long'
            
        Returns:
            A learning path object
        """
        # Define timeframe durations in weeks
        timeframes = {
            'short': 4,   # 1 month
            'medium': 12, # 3 months
            'long': 24    # 6 months
        }
        
        # Get courses related to the goal
        goal_courses = list(mongo.db.courses.find(
            {
                '$or': [
                    {'category': {'$regex': goal, '$options': 'i'}},
                    {'tags': {'$regex': goal, '$options': 'i'}},
                    {'title': {'$regex': goal, '$options': 'i'}},
                    {'description': {'$regex': goal, '$options': 'i'}}
                ]
            },
            {
                'title': 1,
                'difficulty': 1,
                'estimated_duration': 1
            }
        ))
        
        # Sort courses by difficulty
        beginner_courses = [c for c in goal_courses if c.get('difficulty') == 'beginner']
        intermediate_courses = [c for c in goal_courses if c.get('difficulty') == 'intermediate']
        advanced_courses = [c for c in goal_courses if c.get('difficulty') == 'advanced']
        
        # Create learning path based on timeframe
        weeks = timeframes.get(timeframe, 12)
        path_items = []
        
        # Add beginner courses
        for i, course in enumerate(beginner_courses[:2]):
            path_items.append({
                "item_id": str(course['_id']),
                "item_type": "course",
                "order": i,
                "completed": False,
                "estimated_time": course.get('estimated_duration', 120)  # Default to 2 hours
            })
        
        # Add intermediate courses for medium and long timeframes
        if weeks >= 8:
            for i, course in enumerate(intermediate_courses[:2]):
                path_items.append({
                    "item_id": str(course['_id']),
                    "item_type": "course",
                    "order": len(path_items) + i,
                    "completed": False,
                    "estimated_time": course.get('estimated_duration', 180)  # Default to 3 hours
                })
        
        # Add advanced courses for long timeframes
        if weeks >= 16:
            for i, course in enumerate(advanced_courses[:2]):
                path_items.append({
                    "item_id": str(course['_id']),
                    "item_type": "course",
                    "order": len(path_items) + i,
                    "completed": False,
                    "estimated_time": course.get('estimated_duration', 240)  # Default to 4 hours
                })
        
        # Create a learning path document
        learning_path = {
            "user_id": user_id,
            "goal": goal,
            "estimated_duration": weeks,
            "created_at": datetime.utcnow(),
            "items": path_items
        }
        
        # Save the learning path to the database
        result = mongo.db.learning_paths.insert_one(learning_path)
        
        # Return the learning path with the ID
        learning_path['_id'] = str(result.inserted_id)
        return learning_path