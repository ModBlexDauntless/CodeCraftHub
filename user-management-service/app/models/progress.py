# File: app/models/progress.py

from datetime import datetime
from bson import ObjectId

# User progress document structure
progress_schema = {
    "user_id": ObjectId,         # Reference to user
    "course_id": ObjectId,       # Reference to course
    "progress_percentage": float,
    "last_accessed": datetime,
    "completed": bool,
    
    # Analytics data
    "time_spent": int,           # in seconds
    "quiz_scores": dict,         # Dictionary mapping quiz IDs to scores
    
    # We'll store content progress as a nested array
    "content_progress": [
        {
            "content_id": str,    # ID constructed as module_index:content_index
            "viewed": bool,
            "completed": bool,
            "time_spent": int,    # in seconds
            "last_accessed": datetime
        }
    ]
}

def create_progress_document(user_id, course_id):
    """Create a new progress document."""
    return {
        "user_id": ObjectId(user_id),
        "course_id": ObjectId(course_id),
        "progress_percentage": 0.0,
        "last_accessed": datetime.utcnow(),
        "completed": False,
        "time_spent": 0,
        "quiz_scores": {},
        "content_progress": []
    }

def create_content_progress(content_id):
    """Create a content progress entry to be embedded in a progress document."""
    return {
        "content_id": content_id,
        "viewed": False,
        "completed": False,
        "time_spent": 0,
        "last_accessed": datetime.utcnow()
    }
    