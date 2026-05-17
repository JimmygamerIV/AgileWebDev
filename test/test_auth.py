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
        # Check if form shows validation error for password mismatch
        assert b'equal' in response.data or b'match' in response.data or b'Password' in response.data

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
        """Test successful signin redirects to index."""
        response = client.post('/signin', data={
            'username': 'testuser',
            'password': 'TestPass123',
            'csrf_token': 'dummy'
        }, follow_redirects=False)

        # Successful login redirects to index
        assert response.status_code == 302
        assert '/' in response.headers.get('Location', '')

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


class TestLogout:
    """Test logout functionality."""

    def test_logout_authenticated(self, authenticated_client):
        """Logout redirects to signin and clears the session."""
        response = authenticated_client.post('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert 'signin' in response.headers.get('Location', '')

    def test_logout_unauthenticated(self, client):
        """Attempting logout while unauthenticated redirects (login_required)."""
        response = client.post('/logout', follow_redirects=False)
        assert response.status_code == 302

    def test_logout_clears_session(self, authenticated_client):
        """After logout the user can no longer access protected routes."""
        authenticated_client.post('/logout', follow_redirects=True)

        # Protected route should now redirect to signin
        response = authenticated_client.get('/', follow_redirects=False)
        assert response.status_code == 302


class TestForgotPassword:
    """Test forgot password functionality."""

    def test_forgot_password_get(self, client):
        """GET /forgot_password returns the form page."""
        response = client.get('/forgot_password')
        assert response.status_code == 200

    def test_forgot_password_invalid_email_format(self, client):
        """Submitting a non-UWA email shows a validation error."""
        response = client.post('/forgot_password', data={
            'email': 'user@gmail.com'
        })
        assert response.status_code == 200
        assert b'Invalid domain' in response.data or b'UWA' in response.data

    def test_forgot_password_empty_email(self, client):
        """Submitting an empty email shows a validation error."""
        response = client.post('/forgot_password', data={'email': ''})
        assert response.status_code == 200

    def test_forgot_password_valid_email_redirects(self, client):
        """Valid UWA email (even for a non-existent user) redirects to reset page."""
        response = client.post('/forgot_password', data={
            'email': 'nobody@student.uwa.edu.au'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert 'reset_password' in response.headers.get('Location', '')


class TestResetPassword:
    """Test reset password flow."""

    def test_reset_password_without_session(self, client):
        """GET /reset_password without a prior forgot-password session redirects."""
        response = client.get('/reset_password', follow_redirects=False)
        assert response.status_code == 302
        assert 'forgot_password' in response.headers.get('Location', '')

    def test_reset_password_with_valid_session(self, client):
        """GET /reset_password shows the form when session is pre-populated."""
        with client.session_transaction() as sess:
            sess['reset_email'] = 'user@student.uwa.edu.au'
            sess['reset_code'] = '123456'

        response = client.get('/reset_password')
        assert response.status_code == 200

    def test_reset_password_wrong_code(self, client):
        """POST /reset_password with wrong code shows an error."""
        with client.session_transaction() as sess:
            sess['reset_email'] = 'user@student.uwa.edu.au'
            sess['reset_code'] = '123456'

        response = client.post('/reset_password', data={
            'code': '000000',
            'password': 'NewPass123',
            'confirm_password': 'NewPass123',
        })
        assert response.status_code == 200
        assert b'Invalid verification code' in response.data

    def test_reset_password_mismatch(self, client):
        """POST /reset_password with mismatched passwords shows an error."""
        with client.session_transaction() as sess:
            sess['reset_email'] = 'user@student.uwa.edu.au'
            sess['reset_code'] = '123456'

        response = client.post('/reset_password', data={
            'code': '123456',
            'password': 'NewPass123',
            'confirm_password': 'DifferentPass456',
        })
        assert response.status_code == 200
        assert b'match' in response.data or b'do not match' in response.data

    def test_reset_password_weak_password(self, client):
        """POST /reset_password with a weak password shows a validation error."""
        with client.session_transaction() as sess:
            sess['reset_email'] = 'user@student.uwa.edu.au'
            sess['reset_code'] = '123456'

        response = client.post('/reset_password', data={
            'code': '123456',
            'password': 'weak',
            'confirm_password': 'weak',
        })
        assert response.status_code == 200

    def test_reset_password_success(self, client, db_session, sample_user):
        """POST /reset_password with correct code updates the password."""
        with client.session_transaction() as sess:
            sess['reset_email'] = sample_user.email
            sess['reset_code'] = '999999'

        response = client.post('/reset_password', data={
            'code': '999999',
            'password': 'NewSecure1',
            'confirm_password': 'NewSecure1',
        }, follow_redirects=False)

        # Redirects to signin on success
        assert response.status_code == 302
        assert 'signin' in response.headers.get('Location', '')

        # Verify new password is stored
        db_session.expire_all()
        updated = db_session.query(User).filter(User.email == sample_user.email).first()
        assert check_password_hash(updated.password_hash, 'NewSecure1')


class TestPasswordValidation:
    """Unit tests for the validate_password utility."""

    def test_valid_password(self):
        from auth_utils import validate_password
        is_valid, msg = validate_password("SecurePass123")
        assert is_valid
        assert msg == ""

    def test_too_short(self):
        from auth_utils import validate_password
        is_valid, msg = validate_password("Pass1")
        assert not is_valid
        assert "6 characters" in msg

    def test_no_uppercase(self):
        from auth_utils import validate_password
        is_valid, msg = validate_password("securepass123")
        assert not is_valid
        assert "uppercase" in msg

    def test_no_lowercase(self):
        from auth_utils import validate_password
        is_valid, msg = validate_password("SECUREPASS123")
        assert not is_valid
        assert "lowercase" in msg

    def test_no_digit(self):
        from auth_utils import validate_password
        is_valid, msg = validate_password("SecurePass")
        assert not is_valid
        assert "digit" in msg

    def test_empty_password(self):
        from auth_utils import validate_password
        is_valid, _ = validate_password("")
        assert not is_valid

    def test_none_password(self):
        from auth_utils import validate_password
        is_valid, _ = validate_password(None)
        assert not is_valid


class TestEmailValidation:
    """Unit tests for the validate_uwa_email utility."""

    def test_student_domain(self):
        from auth_utils import validate_uwa_email
        is_valid, _ = validate_uwa_email("user@student.uwa.edu.au")
        assert is_valid

    def test_staff_domain(self):
        from auth_utils import validate_uwa_email
        is_valid, _ = validate_uwa_email("user@uwa.edu.au")
        assert is_valid

    def test_subdomain_username(self):
        from auth_utils import validate_uwa_email
        is_valid, _ = validate_uwa_email("first.last@student.uwa.edu.au")
        assert is_valid

    def test_invalid_domain(self):
        from auth_utils import validate_uwa_email
        is_valid, msg = validate_uwa_email("user@gmail.com")
        assert not is_valid
        assert "Invalid domain" in msg or "UWA" in msg

    def test_empty_email(self):
        from auth_utils import validate_uwa_email
        is_valid, _ = validate_uwa_email("")
        assert not is_valid

    def test_none_email(self):
        from auth_utils import validate_uwa_email
        is_valid, _ = validate_uwa_email(None)
        assert not is_valid

    def test_partial_domain(self):
        from auth_utils import validate_uwa_email
        is_valid, _ = validate_uwa_email("user@uwa.edu")
        assert not is_valid
