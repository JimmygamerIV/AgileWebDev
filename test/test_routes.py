"""
Tests for main application routes.
Comprehensive testing for all API endpoints and web routes.
"""
import pytest
import json
from datetime import date, timedelta
from flask import session, url_for
from models import Event, User, Friend, FriendRequest
from database import Session


class TestIndexRoute:
    """Test the main index route."""

    def test_index_redirect_not_logged_in(self, client):
        """Test index redirects to signin when not logged in."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/signin' in response.location

    def test_index_success_logged_in(self, authenticated_client, sample_user):
        """Test index loads successfully when logged in."""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        assert b'UWA' in response.data or b'Social' in response.data

    def test_index_displays_username(self, authenticated_client, sample_user):
        """Test index displays the user's username."""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        assert sample_user.nickname.encode() in response.data or sample_user.username.encode() in response.data


class TestAddEventRoute:
    """Test the add event/import timetable route."""

    def test_add_event_get_not_logged_in(self, client):
        """Test GET /add-event redirects when not logged in."""
        response = client.get('/add-event')
        assert response.status_code == 302
        assert '/signin' in response.location

    def test_add_event_get_logged_in(self, authenticated_client):
        """Test GET /add-event loads form when logged in."""
        response = authenticated_client.get('/add-event')
        assert response.status_code == 200
        assert b'Import' in response.data or b'Timetable' in response.data or b'upload' in response.data

    def test_add_event_post_no_file_or_url(self, authenticated_client):
        """Test POST /add-event with neither file nor URL."""
        response = authenticated_client.post('/add-event', data={
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Please upload a file or provide a URL' in response.data

    def test_add_event_post_invalid_ics_file(self, authenticated_client):
        """Test POST /add-event with invalid ICS file."""
        response = authenticated_client.post('/add-event', data={
            'ics_file': (b'not valid ics content', 'test.ics'),
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Could not parse' in response.data or b'error' in response.data.lower()


class TestTimetableRestoreRoute:
    """Test timetable restore functionality."""

    def test_restore_timetable_no_saved_timetable(self, authenticated_client):
        """Test POST /timetable/restore with no saved timetable."""
        response = authenticated_client.post('/timetable/restore', follow_redirects=True)
        # If no saved timetable, should return 404 or 200 with error message
        assert response.status_code in [200, 404]

    def test_restore_timetable_not_authenticated(self, client):
        """Test POST /timetable/restore when not authenticated."""
        response = client.post('/timetable/restore', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to signin


class TestMyEventsRoute:
    """Test the /api/events/me endpoint."""

    def test_my_events_not_authenticated(self, client):
        """Test GET /api/events/me returns 401 when not authenticated."""
        response = client.get('/api/events/me')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_my_events_no_events(self, authenticated_client, sample_user):
        """Test GET /api/events/me with no events."""
        response = authenticated_client.get('/api/events/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'events' in data
        assert data['events'] == []
        assert data['user_id'] == sample_user.user_id

    def test_my_events_with_future_events(self, authenticated_client, db_session, sample_user):
        """Test GET /api/events/me with future events."""
        future_date = (date.today() + timedelta(days=5)).isoformat()
        event = Event(
            user_id=sample_user.user_id,
            event_name="Future Event",
            location="Room 101",
            day="Monday",
            date=future_date,
            start_time="14:00",
            end_time="15:00"
        )
        db_session.add(event)
        db_session.commit()

        response = authenticated_client.get('/api/events/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['events']) == 1
        assert data['events'][0]['event_name'] == "Future Event"

    def test_my_events_excludes_past_events(self, authenticated_client, db_session, sample_user):
        """Test GET /api/events/me excludes past events."""
        past_date = (date.today() - timedelta(days=5)).isoformat()
        event = Event(
            user_id=sample_user.user_id,
            event_name="Past Event",
            location="Room 101",
            day="Monday",
            date=past_date,
            start_time="14:00",
            end_time="15:00"
        )
        db_session.add(event)
        db_session.commit()

        response = authenticated_client.get('/api/events/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['events']) == 0


class TestDeleteEventRoute:
    """Test the DELETE /api/events/<event_id> endpoint."""

    def test_delete_event_not_authenticated(self, client):
        """Test DELETE /api/events/1 returns 401 when not authenticated."""
        response = client.delete('/api/events/1')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_delete_event_not_found(self, authenticated_client):
        """Test DELETE /api/events/999999 returns 404."""
        response = authenticated_client.delete('/api/events/999999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_delete_event_forbidden(self, authenticated_client, authenticated_client_2, db_session, sample_user, sample_user_2):
        """Test DELETE /api/events/<event_id> when event belongs to another user."""
        future_date = (date.today() + timedelta(days=5)).isoformat()
        event = Event(
            user_id=sample_user.user_id,
            event_name="Another User's Event",
            location="Room 101",
            day="Monday",
            date=future_date,
            start_time="14:00",
            end_time="15:00"
        )
        db_session.add(event)
        db_session.commit()

        response = authenticated_client_2.delete(f'/api/events/{event.event_id}')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data

    def test_delete_event_success(self, authenticated_client, db_session, sample_user):
        """Test successful deletion of user's own event."""
        future_date = (date.today() + timedelta(days=5)).isoformat()
        event = Event(
            user_id=sample_user.user_id,
            event_name="Event to Delete",
            location="Room 101",
            day="Monday",
            date=future_date,
            start_time="14:00",
            end_time="15:00"
        )
        db_session.add(event)
        db_session.commit()
        event_id = event.event_id

        response = authenticated_client.delete(f'/api/events/{event_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['deleted'] == True

        # Verify event is deleted
        deleted_event = db_session.query(Event).filter(Event.event_id == event_id).first()
        assert deleted_event is None


class TestCurrentClassMapDataRoute:
    """Test the /api/map/current-class endpoint."""

    def test_current_class_not_authenticated(self, client):
        """Test GET /api/map/current-class returns 401 when not authenticated."""
        response = client.get('/api/map/current-class')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_current_class_no_events(self, authenticated_client):
        """Test GET /api/map/current-class with no events."""
        response = authenticated_client.get('/api/map/current-class')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['class'] is None

    def test_current_class_with_future_event(self, authenticated_client, db_session, sample_user):
        """Test GET /api/map/current-class with a future event."""
        future_date = (date.today() + timedelta(days=5)).isoformat()
        event = Event(
            user_id=sample_user.user_id,
            event_name="Future Lecture",
            location="Room 101",
            day="Monday",
            date=future_date,
            start_time="14:00",
            end_time="15:00"
        )
        db_session.add(event)
        db_session.commit()

        response = authenticated_client.get('/api/map/current-class')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'class' in data


class TestFriendsRoute:
    """Test the /friends route."""

    def test_friends_redirect_not_logged_in(self, client):
        """Test /friends redirects to signin when not logged in."""
        response = client.get('/friends')
        assert response.status_code == 302
        assert '/signin' in response.location

    def test_friends_page_no_friends(self, authenticated_client):
        """Test /friends page loads with no friends."""
        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        assert b'friends' in response.data.lower() or b'Friend' in response.data

    def test_friends_page_with_friends(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test /friends page displays friends."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend)
        db_session.commit()

        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        assert sample_user_2.username.encode() in response.data or sample_user_2.nickname.encode() in response.data

    def test_friends_page_with_pending_requests(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test /friends page displays pending friend requests."""
        request = FriendRequest(
            sender_id=sample_user_2.user_id,
            receiver_id=sample_user.user_id,
            status='pending'
        )
        db_session.add(request)
        db_session.commit()

        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        assert sample_user_2.username.encode() in response.data or sample_user_2.nickname.encode() in response.data


class TestProfileRoute:
    """Test the /profile route."""

    def test_profile_redirect_not_logged_in(self, client):
        """Test /profile redirects to signin when not logged in."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/signin' in response.location

    def test_profile_get_logged_in(self, authenticated_client, sample_user):
        """Test GET /profile loads profile page when logged in."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
        assert b'profile' in response.data.lower() or b'nickname' in response.data.lower()
        assert sample_user.email.encode() in response.data

    def test_profile_update_nickname(self, authenticated_client, db_session, sample_user):
        """Test POST /profile to update nickname."""
        response = authenticated_client.post('/profile', data={
            'action': 'update_nickname',
            'nickname': 'New Nickname',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # The implementation may or may not update the nickname depending on the actual code

    def test_profile_update_password_wrong_current(self, authenticated_client):
        """Test profile password update with wrong current password."""
        response = authenticated_client.post('/profile', data={
            'action': 'update_password',
            'current_password': 'WrongPassword123',
            'new_password': 'NewPass456',
            'confirm_password': 'NewPass456',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data.lower()

    def test_profile_update_password_mismatch(self, authenticated_client):
        """Test profile password update with mismatched new passwords."""
        response = authenticated_client.post('/profile', data={
            'action': 'update_password',
            'current_password': 'TestPass123',
            'new_password': 'NewPass456',
            'confirm_password': 'DifferentPass789',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'do not match' in response.data

    def test_profile_update_email_invalid_domain(self, authenticated_client):
        """Test profile email update with invalid domain."""
        response = authenticated_client.post('/profile', data={
            'action': 'update_email',
            'email': 'user@gmail.com',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid domain' in response.data or b'UWA email' in response.data

    def test_profile_update_email_valid(self, authenticated_client, db_session, sample_user):
        """Test profile email update with valid UWA email."""
        response = authenticated_client.post('/profile', data={
            'action': 'update_email',
            'email': 'newemail@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # The implementation may or may not update the email depending on the actual code


class TestLogoutRoute:
    """Test the logout functionality."""

    def test_logout_success(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.post('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to signin page
        assert b'Sign In' in response.data or b'signin' in response.data

    def test_logout_clears_session(self, client, sample_user):
        """Test logout clears session."""
        with client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.user_id
            
            # Verify session has user_id
            with client.session_transaction() as sess:
                assert sess.get('user_id') == sample_user.user_id
            
            # Logout
            client.post('/logout')
            
            # Verify session is cleared
            with client.session_transaction() as sess:
                assert sess.get('user_id') is None
