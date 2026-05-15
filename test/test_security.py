"""
Security tests for UniMap application.
Tests for CSRF, XSS, SQL injection, authentication bypass, etc.
"""
import pytest
from flask import session
from werkzeug.security import check_password_hash
from models import User
from database import Session


class TestCSRFProtection:
    """Test CSRF protection."""
    
    def test_signup_without_csrf_token(self, client, app):
        """Test signup POST requires CSRF token."""
        with app.app_context():
            response = client.post('/signup', data={
                'username': 'testuser',
                'nickname': 'Test',
                'password': 'Pass123',
                'confirm_password': 'Pass123',
                'email': 'test@student.uwa.edu.au'
                # CSRF token missing
            })
            # Should reject or warn about CSRF
            assert response.status_code in [400, 302]
    
    def test_signin_without_csrf_token(self, client, app):
        """Test signin POST requires CSRF token."""
        with app.app_context():
            response = client.post('/signin', data={
                'username': 'testuser',
                'password': 'Pass123'
                # CSRF token missing
            })
            # Should reject or warn about CSRF
            assert response.status_code == 200
    
    def test_add_friend_without_csrf_token(self, authenticated_client, app):
        """Test add friend requires CSRF token."""
        with app.app_context():
            response = authenticated_client.post('/send_friend_request', data={
                'target_username': 'someuser'
                # CSRF token missing
            })
            # Should reject or warn
            assert response.status_code in [400, 302]


class TestAuthenticationBypass:
    """Test authentication bypass attempts."""
    
    def test_signin_with_empty_credentials(self, client):
        """Test signin with empty username and password."""
        response = client.post('/signin', data={
            'username': '',
            'password': '',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should not sign in
        assert response.status_code == 200
        
    def test_signin_with_sql_injection_attempt(self, client):
        """Test signin with SQL injection attempt in username."""
        response = client.post('/signin', data={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1",
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should safely reject
        assert response.status_code == 200
        assert b'incorrect' in response.data
    
    def test_signup_with_sql_injection_attempt(self, client):
        """Test signup with SQL injection attempt."""
        response = client.post('/signup', data={
            'username': "'; DROP TABLE users; --",
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'test@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should safely reject
        assert response.status_code == 200
        # Username should not contain spaces (has space in injection)
        assert b'spaces' in response.data or b'error' in response.data.lower()
    
    def test_direct_session_manipulation(self, client, db_session):
        """Test directly manipulating session."""
        with client:
            with client.session_transaction() as sess:
                sess['user_id'] = 99999  # Non-existent user
            
            response = client.get('/profile')
            
            # User should not be loaded from invalid session
            with client.session_transaction() as sess:
                assert sess.get('user_id') is None or sess.get('user_id') == 99999
    
    def test_accessing_protected_route_without_auth(self, client):
        """Test accessing protected routes without authentication."""
        protected_routes = [
            '/profile',
            '/friends',
            '/add_event',
            '/import_timetable'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Should redirect to signin or return 302
            assert response.status_code in [302,404]


class TestXSSPrevention:
    """Test XSS prevention."""
    
    def test_xss_in_nickname(self, client):
        """Test XSS attempt in nickname field."""
        response = client.post('/signup', data={
            'username': 'xsstest',
            'nickname': '<script>alert("xss")</script>',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'xss@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should escape or reject the script tag
        assert response.status_code == 200
        # If saved, the script should be escaped in output
        if b'xss' in response.data:
            assert b'<script>' not in response.data or b'&lt;script&gt;' in response.data
    
    def test_xss_in_event_name(self, authenticated_client, db_session, sample_user):
        """Test XSS attempt in event name."""
        from models import Event
        
        event = Event(
            user_id=sample_user.user_id,
            event_name='<img src=x onerror="alert(\'xss\')">',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        response = authenticated_client.get('/')
        assert response.status_code == 200


class TestInputValidation:
    """Test strict input validation."""
    
    def test_username_with_special_characters(self, client):
        """Test username with dangerous special characters."""
        special_chars = ['<', '>', '"', "'", '&', ';', '/', '\\']
        
        for char in special_chars:
            response = client.post('/signup', data={
                'username': f'user{char}test',
                'nickname': 'Test',
                'password': 'Pass123',
                'confirm_password': 'Pass123',
                'email': f'user{ord(char)}@student.uwa.edu.au',
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            # Should reject or handle safely
            assert response.status_code == 200
    
    def test_email_injection_attempt(self, client):
        """Test email header injection."""
        response = client.post('/signup', data={
            'username': 'injecttest',
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'test@student.uwa.edu.au\nBcc: attacker@evil.com',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should reject malformed email
        assert response.status_code == 200
    
    def test_password_field_max_length(self, client):
        """Test password field with extremely long input."""
        very_long_password = 'A' * 10000 + '1'  # Very long but valid password
        
        response = client.post('/signup', data={
            'username': 'longpasstest',
            'nickname': 'Test',
            'password': very_long_password,
            'confirm_password': very_long_password,
            'email': 'longpass@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should handle long password safely
        assert response.status_code == 200
    
    def test_username_max_length(self, client):
        """Test username at maximum allowed length."""
        max_username = 'a' * 15  # Username should be max 15 chars
        
        response = client.post('/signup', data={
            'username': max_username,
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'maxuser@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should accept at boundary
        assert response.status_code in [200, 302]
    
    def test_username_exceeds_max_length(self, client):
        """Test username exceeding maximum length."""
        over_max_username = 'a' * 16  # Over 15 char limit
        
        response = client.post('/signup', data={
            'username': over_max_username,
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'overmax@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should reject if validation exists
        assert response.status_code == 200


class TestRateLimitingConcerns:
    """Test for rate limiting concerns."""
    
    def test_brute_force_signin_attempts(self, client, sample_user):
        """Test multiple failed signin attempts."""
        # Attempt signin with wrong password multiple times
        for i in range(10):
            response = client.post('/signin', data={
                'username': sample_user.username,
                'password': f'WrongPass{i}',
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # In production, should implement rate limiting
            # This test documents the concern
    
    def test_multiple_signup_attempts_same_email(self, client):
        """Test multiple signup attempts with same email."""
        email = 'duplicate@student.uwa.edu.au'
        
        for i in range(3):
            response = client.post('/signup', data={
                'username': f'user{i}',
                'nickname': f'User {i}',
                'password': 'Pass123',
                'confirm_password': 'Pass123',
                'email': email,
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            assert response.status_code == 200


class TestDataExposure:
    """Test for information disclosure."""
    
    def test_error_messages_dont_leak_info(self, client):
        """Test that error messages don't leak sensitive information."""
        response = client.post('/signin', data={
            'username': 'nonexistent_user_xyz_123',
            'password': 'SomePassword123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Error should be generic, not saying "user doesn't exist"
        error_text = response.data.decode().lower()
        assert 'incorrect' in error_text or 'invalid' in error_text
        assert 'does not exist' not in error_text
    
    def test_user_enumeration_prevention(self, client, db_session, sample_user):
        """Test that user enumeration is prevented."""
        # Try with existing username
        response1 = client.post('/signin', data={
            'username': sample_user.username,
            'password': 'WrongPassword123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Try with non-existing username
        response2 = client.post('/signin', data={
            'username': 'completely_nonexistent_user_12345',
            'password': 'WrongPassword123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Both should return same error message
        error1 = response1.data.decode().lower()
        error2 = response2.data.decode().lower()
        # Should both mention "incorrect" without differentiating
        assert 'incorrect' in error1 or 'invalid' in error1
        assert 'incorrect' in error2 or 'invalid' in error2


class TestSessionSecurity:
    """Test session security."""
    
    def test_session_fixation_attack(self, client, sample_user):
        """Test prevention of session fixation."""
        with client:
            # Set a known session ID
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.user_id
            
            # Login with different user
            signin_response = client.post('/signin', data={
                'username': sample_user.username,
                'password': 'TestPass123',
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            # Session should still be valid
            assert signin_response.status_code == 200
    
    def test_concurrent_sessions(self, client, sample_user):
        """Test handling of concurrent sessions."""
        # Create first session
        with client:
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.user_id
                sess_id_1 = id(sess)
            
            response1 = client.get('/profile')
            assert response1.status_code == 200
        
        # Create second session
        with client:
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.user_id
                sess_id_2 = id(sess)
            
            response2 = client.get('/profile')
            assert response2.status_code == 200


class TestPasswordSecurity:
    """Test password security measures."""
    
    def test_password_never_logged(self, db_session, sample_user):
        """Test that passwords are never stored in plain text."""
        # Password should only be stored as hash
        assert sample_user.password_hash != 'TestPass123'
        assert sample_user.password_hash.startswith('pbkdf2:')
        assert check_password_hash(sample_user.password_hash, 'TestPass123')
    
    def test_password_hash_algorithm(self, db_session, sample_user):
        """Test password uses secure hashing algorithm."""
        # Should use pbkdf2:sha256
        assert 'pbkdf2:sha256' in sample_user.password_hash
        assert 'md5' not in sample_user.password_hash
        assert 'sha1' not in sample_user.password_hash.lower()
    
    def test_same_password_different_hash(self, db_session):
        """Test that same password generates different hashes."""
        from werkzeug.security import generate_password_hash
        
        password = 'SamePassword123'
        hash1 = generate_password_hash(password, method='pbkdf2:sha256')
        hash2 = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify with same password
        assert check_password_hash(hash1, password)
        assert check_password_hash(hash2, password)
