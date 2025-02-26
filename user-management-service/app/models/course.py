# File: app/models/course.py

from datetime import datetime

# Course document structure
course_schema = {
    "title": str,
    "description": str,
    "created_at": datetime,
    "updated_at": datetime,
    
    # Course metadata for personalization
    "difficulty": str,           # beginner, intermediate, advanced
    "category": str,
    "tags": list,                # list of tags
    "estimated_duration": int,   # in minutes
    
    # Nested array of modules
    "modules": [
        {
            "title": str,
            "description": str,
            "order": int,        # Sequence in the course
            
            # Nested array of content items
            "content_items": [
                {
                    "title": str,
                    "content_type": str,  # video, text, quiz, etc.
                    "content_url": str,   # URL to content or file path
                    "order": int,         # Sequence in the module
                    
                    # Metadata for personalization
                    "difficulty": str,
                    "learning_style": str,
                    "estimated_time": int  # in minutes
                }
            ]
        }
    ]
}

def create_course_document(title, description, difficulty, category, tags=None, 
                          estimated_duration=0):
    """Create a new course document."""
    return {
        "title": title,
        "description": description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "difficulty": difficulty,
        "category": category,
        "tags": tags or [],
        "estimated_duration": estimated_duration,
        "modules": []
    }

def create_module_document(title, description, order):
    """Create a new module document to be embedded in a course."""
    return {
        "title": title,
        "description": description,
        "order": order,
        "content_items": []
    }

def create_content_item_document(title, content_type, content_url, order, 
                                difficulty=None, learning_style=None, estimated_time=0):
    """Create a new content item document to be embedded in a module."""
    return {
        "title": title,
        "content_type": content_type,
        "content_url": content_url,
        "order": order,
        "difficulty": difficulty,
        "learning_style": learning_style,
        "estimated_time": estimated_time
    }