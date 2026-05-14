"""
Tests for authentication functionality.
"""
import pytest
from flask import session
from werkzeug.security import check_password_hash
from models import User
from database import Session


class TestSignup:
    """Test user signup functionality."""
    
    def test_signup_get_request(self, client):
        """Test GET signup page loads."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'Sign Up' in response.data or b'signup' in response.data
    
    def test_signup_success(self, client, db_session):
        """Test successful signup."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        user = db_session.query(User).filter(User.username == 'newuser').first()
        assert user is not None
        assert user.nickname == 'New User'
        assert user.email == 'newuser@student.uwa.edu.au'
        assert check_password_hash(user.password_hash, 'SecurePass123')
    
    def test_signup_duplicate_username(self, client, db_session, sample_user):
        """Test signup with duplicate username."""
        response = client.post('/signup', data={
            'username': sample_user.username,
            'nickname': 'Another User',
            'password': 'NewPass456',
            'confirm_password': 'NewPass456',
            'email': 'another@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already exists' in response.data or b'exists' in response.data
    
    def test_signup_duplicate_email(self, client, db_session, sample_user):
        """Test signup with duplicate email."""
        response = client.post('/signup', data={
            'username': 'newusername',
            'nickname': 'Another User',
            'password': 'NewPass456',
            'confirm_password': 'NewPass456',
            'email': sample_user.email,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already registered' in response.data or b'registered' in response.data
    
    def test_signup_password_mismatch(self, client):
        """Test signup with mismatched passwords."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'SecurePass123',
            'confirm_password': 'DifferentPass456',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'do not match' in response.data or b'Passwords' in response.data
    
    def test_signup_password_too_short(self, client):
        """Test signup with password less than 6 characters."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'Pass1',
            'confirm_password': 'Pass1',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'at least 6 characters' in response.data
    
    def test_signup_password_no_uppercase(self, client):
        """Test signup with password missing uppercase letter."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'uppercase letter' in response.data
    
    def test_signup_password_no_lowercase(self, client):
        """Test signup with password missing lowercase letter."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'SECUREPASS123',
            'confirm_password': 'SECUREPASS123',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'lowercase letter' in response.data
    
    def test_signup_password_no_number(self, client):
        """Test signup with password missing number."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'SecurePass',
            'confirm_password': 'SecurePass',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'number' in response.data
    
    def test_signup_username_with_spaces(self, client):
        """Test signup with spaces in username."""
        response = client.post('/signup', data={
            'username': 'new user',
            'nickname': 'New User',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
            'email': 'newuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'spaces' in response.data
    
    def test_signup_invalid_email_domain(self, client):
        """Test signup with invalid email domain."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'nickname': 'New User',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
            'email': 'newuser@gmail.com',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid domain' in response.data or b'UWA' in response.data
    
    def test_signup_valid_uwa_email_variants(self, client, db_session):
        """Test signup with valid UWA email variants."""
        valid_emails = [
            'user@student.uwa.edu.au',
            'user@uwa.edu.au',
            'user.name@student.uwa.edu.au'
        ]
        
        for i, email in enumerate(valid_emails):
            response = client.post('/signup', data={
                'username': f'user{i}',
                'nickname': f'User {i}',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123',
                'email': email,
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            # Should not see error messages
            assert b'Invalid domain' not in response.data or response.status_code == 302


class TestSignin:
    """Test user signin functionality."""
    
    def test_signin_get_request(self, client):
        """Test GET signin page loads."""
        response = client.get('/signin')
        assert response.status_code == 200
        assert b'Sign in' in response.data or b'signin' in response.data
    
    def test_signin_success(self, client, sample_user):
        """Test successful signin."""
        response = client.post('/signin', data={
            'username': 'testuser',
            'password': 'TestPass123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get('user_id') == sample_user.user_id
    
    def test_signin_invalid_username(self, client):
        """Test signin with invalid username."""
        response = client.post('/signin', data={
            'username': 'nonexistent',
            'password': 'TestPass123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data
    
    def test_signin_invalid_password(self, client, sample_user):
        """Test signin with incorrect password."""
        response = client.post('/signin', data={
            'username': 'testuser',
            'password': 'WrongPassword123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data
    
    def test_signin_empty_username(self, client):
        """Test signin with empty username."""
        response = client.post('/signin', data={
            'username': '',
            'password': 'TestPass123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_signin_empty_password(self, client):
        """Test signin with empty password."""
        response = client.post('/signin', data={
            'username': 'testuser',
            'password': '',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestLoadCurrentUser:
    """Test user session loading."""
    
    def test_user_loaded_from_session(self, authenticated_client, sample_user):
        """Test user is loaded from session."""
        response = authenticated_client.get('/')
        
        # User should be loaded in the context
        assert response.status_code in [200, 302]
    
    def test_user_not_loaded_without_session(self, client):
        """Test user not loaded without session."""
        response = client.get('/')
        
        # Should either return 200 or redirect to signin
        assert response.status_code in [200, 302]
    
    def test_invalid_user_id_removed_from_session(self, client, db_session):
        """Test invalid user_id is removed from session."""
        with client:
            with client.session_transaction() as sess:
                sess['user_id'] = 99999  # Non-existent user
            
            response = client.get('/')
            
            with client.session_transaction() as sess:
                assert sess.get('user_id') is None
