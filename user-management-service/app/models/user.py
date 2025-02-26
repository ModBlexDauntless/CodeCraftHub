from datetime import datetime

# User document structure
user_schema = {
    "username": str,  # unique
    "email": str,     # unique
    "password": str,  # hashed
    "created_at": datetime,
    
    # User preferences for personalized learning
    "learning_style": str,       # visual, auditory, reading, kinesthetic
    "difficulty_preference": str, # beginner, intermediate, advanced
    "interests": list,           # list of topic interests
}

def create_user_document(username, email, password, learning_style="visual", 
                        difficulty_preference="beginner", interests=None):
    """Create a new user document."""
    return {
        "username": username,
        "email": email,
        "password": password,
        "created_at": datetime.utcnow(),
        "learning_style": learning_style,
        "difficulty_preference": difficulty_preference,
        "interests": interests or [],
    }