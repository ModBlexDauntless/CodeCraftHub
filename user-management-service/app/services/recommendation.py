# File: app/services/recommendation.py

from app import mongo
from bson.objectid import ObjectId

class RecommendationService:
    def recommend_courses_for_user(self, user_id, limit=5):
        """
        Recommends courses based on user preferences and behavior.
        
        Args:
            user_id: The ID of the user to make recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended course IDs
        """
        # Get user
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return []
        
        # Get user preferences
        learning_style = user.get('learning_style')
        difficulty = user.get('difficulty_preference')
        interests = user.get('interests', [])
        
        # Get courses the user has already interacted with
        completed_courses = mongo.db.progress.find(
            {
                'user_id': ObjectId(user_id),
                'completed': True
            },
            {'course_id': 1}
        )
        
        completed_course_ids = [str(p['course_id']) for p in completed_courses]
        
        in_progress_courses = mongo.db.progress.find(
            {
                'user_id': ObjectId(user_id),
                'completed': False
            },
            {'course_id': 1}
        )
        
        in_progress_course_ids = [str(p['course_id']) for p in in_progress_courses]
        
        # Find courses that match user preferences
        # We exclude courses the user has already completed
        query = {'_id': {'$nin': [ObjectId(cid) for cid in completed_course_ids]}}
        
        # Apply filters based on preferences
        if difficulty:
            query['difficulty'] = difficulty
        
        # Get all potential courses
        potential_courses = list(mongo.db.courses.find(query))
        
        # Score each course based on relevance to user
        scored_courses = []
        for course in potential_courses:
            score = 0
            
            # Boost score if course matches learning style
            if learning_style and 'modules' in course:
                for module in course['modules']:
                    for item in module.get('content_items', []):
                        if item.get('learning_style') == learning_style:
                            score += 0.5
            
            # Boost score if course category or tags match interests
            if interests:
                for interest in interests:
                    # Match against category
                    if course.get('category') and interest.lower() in course['category'].lower():
                        score += 1
                    
                    # Match against tags
                    if course.get('tags'):
                        if interest.lower() in [tag.lower() for tag in course['tags']]:
                            score += 1
            
            # Penalize score for courses already in progress
            if str(course['_id']) in in_progress_course_ids:
                score *= 0.7
            
            scored_courses.append((str(course['_id']), score))
        
        # Sort by score and get top recommendations
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        return [course_id for course_id, _ in scored_courses[:limit]]
    
    def recommend_next_content(self, user_id, course_id):
        """
        Recommends the next piece of content a user should engage with in a course.
        
        Args:
            user_id: The ID of the user
            course_id: The ID of the course
            
        Returns:
            Dictionary with module_index and content_index or None if course is complete
        """
        # Get the course
        course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
        if not course or 'modules' not in course:
            return None
        
        # Get user progress for this course
        progress = mongo.db.progress.find_one({
            'user_id': ObjectId(user_id),
            'course_id': ObjectId(course_id)
        })
        
        if not progress:
            # User hasn't started this course, recommend the first content item
            for module in sorted(course['modules'], key=lambda m: m['order']):
                if module.get('content_items'):
                    first_content = sorted(module['content_items'], key=lambda c: c['order'])[0]
                    return {
                        'module_index': module['order'],
                        'content_index': first_content['order']
                    }
            return None
        
        # Create a set of completed content IDs
        completed_content_ids = set()
        for cp in progress.get('content_progress', []):
            if cp.get('completed', False):
                completed_content_ids.add(cp['content_id'])
        
        # Find the first uncompleted content item
        for module in sorted(course['modules'], key=lambda m: m['order']):
            module_index = module['order']
            
            for content in sorted(module.get('content_items', []), key=lambda c: c['order']):
                content_index = content['order']
                content_id = f"{module_index}:{content_index}"
                
                if content_id not in completed_content_ids:
                    return {
                        'module_index': module_index,
                        'content_index