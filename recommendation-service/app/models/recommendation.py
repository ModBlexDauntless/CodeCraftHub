from datetime import datetime

# Recommendation document structure
recommendation_schema = {
    "user_id": str,  # ID of the user receiving the recommendation
    "item_id": str,  # ID of the recommended item (course, exercise, etc.)
    "item_type": str,  # Type of the recommended item (course, exercise, article, etc.)
    "reason": str,  # Reason for the recommendation
    "score": float,  # Relevance score (0-1)
    "created_at": datetime,
    "viewed": bool,  # Whether the user has viewed this recommendation
    "clicked": bool  # Whether the user has clicked on this recommendation
}

def create_recommendation_document(user_id, item_id, item_type, reason, score):
    """Create a new recommendation document."""
    return {
        "user_id": user_id,
        "item_id": item_id,
        "item_type": item_type,
        "reason": reason,
        "score": score,
        "created_at": datetime.utcnow(),
        "viewed": False,
        "clicked": False
    }

# Learning path document structure
learning_path_schema = {
    "user_id": str,
    "goal": str,  # Learning goal (e.g., "Python mastery", "Web development")
    "estimated_duration": int,  # Estimated duration in weeks
    "created_at": datetime,
    "items": [
        {
            "item_id": str,
            "item_type": str,
            "order": int,
            "completed": bool,
            "estimated_time": int  # in minutes
        }
    ]
}

def create_learning_path_document(user_id, goal, estimated_duration, items=None):
    """Create a new learning path document."""
    return {
        "user_id": user_id,
        "goal": goal,
        "estimated_duration": estimated_duration,
        "created_at": datetime.utcnow(),
        "items": items or []
    }