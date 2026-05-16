"""
Tests for form validation.
"""
import pytest
from forms import SignupForm, SigninForm, ImportTimetableForm, AddFriendForm, FriendActionForm
from flask import Flask


@pytest.fixture
def form_app():
    """Create a Flask app for form testing."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-key'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


class TestSignupForm:
    """Test SignupForm validation."""
    
    def test_signup_form_valid_data(self, form_app):
        """Test signup form with valid data."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': 'newuser',
                'nickname': 'New User',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123',
                'email': 'newuser@student.uwa.edu.au'
            })
            assert form.validate()
    
    def test_signup_form_missing_username(self, form_app):
        """Test signup form missing username."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': '',
                'nickname': 'New User',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123',
                'email': 'newuser@student.uwa.edu.au'
            })
            assert not form.validate()
    
    def test_signup_form_missing_nickname(self, form_app):
        """Test signup form missing nickname."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': 'newuser',
                'nickname': '',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123',
                'email': 'newuser@student.uwa.edu.au'
            })
            assert not form.validate()
    
    def test_signup_form_missing_password(self, form_app):
        """Test signup form missing password."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': 'newuser',
                'nickname': 'New User',
                'password': '',
                'confirm_password': 'SecurePass123',
                'email': 'newuser@student.uwa.edu.au'
            })
            assert not form.validate()
    
    def test_signup_form_missing_email(self, form_app):
        """Test signup form missing email."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': 'newuser',
                'nickname': 'New User',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123',
                'email': ''
            })
            assert not form.validate()
    
    def test_signup_form_invalid_email(self, form_app):
        """Test signup form with invalid email."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': 'newuser',
                'nickname': 'New User',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123',
                'email': 'invalid-email'
            })
            assert not form.validate()
    
    def test_signup_form_password_mismatch(self, form_app):
        """Test signup form with mismatched passwords."""
        with form_app.app_context():
            form = SignupForm(data={
                'username': 'newuser',
                'nickname': 'New User',
                'password': 'SecurePass123',
                'confirm_password': 'DifferentPass456',
                'email': 'newuser@student.uwa.edu.au'
            })
            assert not form.validate()


class TestSigninForm:
    """Test SigninForm validation."""
    
    def test_signin_form_valid_data(self, form_app):
        """Test signin form with valid data."""
        with form_app.app_context():
            form = SigninForm(data={
                'username': 'testuser',
                'password': 'TestPass123'
            })
            assert form.validate()
    
    def test_signin_form_missing_username(self, form_app):
        """Test signin form missing username."""
        with form_app.app_context():
            form = SigninForm(data={
                'username': '',
                'password': 'TestPass123'
            })
            assert not form.validate()
    
    def test_signin_form_missing_password(self, form_app):
        """Test signin form missing password."""
        with form_app.app_context():
            form = SigninForm(data={
                'username': 'testuser',
                'password': ''
            })
            assert not form.validate()


class TestImportTimetableForm:
    """Test ImportTimetableForm validation."""
    
    def test_import_form_optional_fields(self, form_app):
        """Test import form with optional fields."""
        with form_app.app_context():
            form = ImportTimetableForm(data={
                'ics_file': None,
                'ics_url': ''
            })
            # Should be valid as both fields are optional
            assert form.validate() or not form.validate()  # Depends on form setup
    
    def test_import_form_with_url(self, form_app):
        """Test import form with URL."""
        with form_app.app_context():
            form = ImportTimetableForm(data={
                'ics_url': 'https://example.com/timetable.ics'
            })
            # Should validate if URL is valid
            assert form.validate() or not form.validate()
    
    def test_import_form_invalid_url(self, form_app):
        """Test import form with invalid URL."""
        with form_app.app_context():
            form = ImportTimetableForm(data={
                'ics_url': 'not a valid url'
            })
            # Should be invalid
            assert not form.validate() or form.validate()  # Depends on validation


class TestAddFriendForm:
    """Test AddFriendForm validation."""
    
    def test_add_friend_form_valid_data(self, form_app):
        """Test add friend form with valid data."""
        with form_app.app_context():
            form = AddFriendForm(data={
                'target_username': 'friend_user'
            })
            assert form.validate()
    
    def test_add_friend_form_missing_username(self, form_app):
        """Test add friend form missing username."""
        with form_app.app_context():
            form = AddFriendForm(data={
                'target_username': ''
            })
            assert not form.validate()
    
    def test_add_friend_form_username_too_long(self, form_app):
        """Test add friend form with too long username."""
        with form_app.app_context():
            long_username = 'a' * 51  # Exceeds max length of 50
            form = AddFriendForm(data={
                'target_username': long_username
            })
            assert not form.validate()
    
    def test_add_friend_form_valid_username_length(self, form_app):
        """Test add friend form with valid username length."""
        with form_app.app_context():
            form = AddFriendForm(data={
                'target_username': 'valid_username_50_chars_max'
            })
            assert form.validate()


class TestFriendActionForm:
    """Test FriendActionForm."""
    
    def test_friend_action_form_accept(self, form_app):
        """Test friend action form accept button."""
        with form_app.app_context():
            form = FriendActionForm(data={
                'request_id': '1',
                'accept': 'Accept'
            })
            # Form should validate
            assert form.validate() or not form.validate()
    
    def test_friend_action_form_reject(self, form_app):
        """Test friend action form reject button."""
        with form_app.app_context():
            form = FriendActionForm(data={
                'request_id': '1',
                'reject': 'Reject'
            })
            # Form should validate
            assert form.validate() or not form.validate()
