"""Authentication and authorization utility functions.

This module provides helper functions for common authentication tasks
such as checking permissions, validating credentials, and managing
user sessions.
"""

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from database import Session
from models import User, Friend


def get_current_user_with_db():
    """Get current user object from database.
    
    Returns:
        User: Current user object from database, or None if not authenticated
    """
    if not current_user.is_authenticated:
        return None
    
    db = Session()
    try:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        return user
    finally:
        db.close()


def require_friendship(user_id):
    """Decorator to check if current user is friends with specified user.
    
    Args:
        user_id (int): Target user ID to check friendship with
        
    Returns:
        function: Decorated function that checks friendship
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please sign in to continue.', 'warning')
                return redirect(url_for('auth.signin'))
            
            db = Session()
            try:
                # Check if current_user is friends with target user
                is_friend = db.query(Friend).filter(
                    ((Friend.user_id == current_user.user_id) & 
                     (Friend.friend_id == user_id)) |
                    ((Friend.user_id == user_id) & 
                     (Friend.friend_id == current_user.user_id))
                ).first()
                
                if not is_friend:
                    flash('You are not friends with this user.', 'danger')
                    return redirect(url_for('index'))
                
                return f(*args, **kwargs)
            finally:
                db.close()
        
        return decorated_function
    return decorator


def validate_password(password):
    """Validate password against security requirements.
    
    Requirements:
        - At least 6 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    import re
    
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit (0-9)."
    
    return True, ""


def validate_uwa_email(email):
    """Validate email against UWA domain requirements.
    
    Valid formats:
        - user@student.uwa.edu.au
        - user@uwa.edu.au
    
    Args:
        email (str): Email to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    import re
    
    if not email:
        return False, "Email address cannot be empty."
    
    uwa_email_regex = r'^[a-zA-Z0-9._%+-]+@(student\.)?uwa\.edu\.au$'
    if not re.match(uwa_email_regex, email.strip().lower()):
        return False, "Invalid domain. Please use a valid UWA email (@student.uwa.edu.au or @uwa.edu.au)."
    
    return True, ""


def user_owns_resource(resource, user_id):
    """Check if user owns a resource (event, etc).
    
    Args:
        resource: Resource object with user_id attribute
        user_id (int): User ID to check
        
    Returns:
        bool: True if user owns the resource
    """
    return hasattr(resource, 'user_id') and resource.user_id == user_id
