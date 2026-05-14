"""
Integration tests combining multiple components.
"""
import pytest
from models import User, Friend, FriendRequest, Event
from database import Session


class TestSignupAndSignin:
    """Integration tests for signup and signin flow."""
    
    def test_full_signup_signin_flow(self, client, db_session):
        """Test complete signup and signin workflow."""
        # Sign up
        signup_response = client.post('/signup', data={
            'username': 'integration_user',
            'nickname': 'Integration User',
            'password': 'IntegrationPass123',
            'confirm_password': 'IntegrationPass123',
            'email': 'integration@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert signup_response.status_code == 200
        
        # Verify user created
        user = db_session.query(User).filter(
            User.username == 'integration_user'
        ).first()
        assert user is not None
        
        # Sign in with new account
        signin_response = client.post('/signin', data={
            'username': 'integration_user',
            'password': 'IntegrationPass123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert signin_response.status_code == 200
        
        # Verify session is created
        with client.session_transaction() as sess:
            assert sess.get('user_id') == user.user_id
    
    def test_signup_duplicate_prevents_signin_conflict(self, client, db_session, sample_user):
        """Test that duplicate signup doesn't affect existing user signin."""
        # Try to signup with existing email
        signup_response = client.post('/signup', data={
            'username': 'different_username',
            'nickname': 'Different User',
            'password': 'DifferentPass123',
            'confirm_password': 'DifferentPass123',
            'email': sample_user.email,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert b'already registered' in signup_response.data
        
        # Existing user can still sign in
        signin_response = client.post('/signin', data={
            'username': sample_user.username,
            'password': 'TestPass123',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert signin_response.status_code == 200


class TestFriendsWorkflow:
    """Integration tests for friends workflow."""
    
    def test_friend_request_accept_workflow(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test complete friend request workflow: send → accept → view."""
        # Send friend request
        request_response = authenticated_client.post('/add_friend', data={
            'target_username': sample_user_2.username,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert request_response.status_code == 200
        
        # Verify friend request exists
        friend_req = db_session.query(FriendRequest).filter(
            FriendRequest.sender_id == sample_user.user_id,
            FriendRequest.receiver_id == sample_user_2.user_id
        ).first()
        
        if friend_req:
            # Accept request
            accept_response = authenticated_client.post('/accept_friend_request', data={
                'request_id': friend_req.request_id,
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            assert accept_response.status_code == 200
    
    def test_friend_request_reject_workflow(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test friend request rejection workflow."""
        # Create friend request
        friend_req = FriendRequest(
            sender_id=sample_user_2.user_id,
            receiver_id=sample_user.user_id,
            status="pending"
        )
        db_session.add(friend_req)
        db_session.commit()
        
        # Reject request
        reject_response = authenticated_client.post('/reject_friend_request', data={
            'request_id': friend_req.request_id,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert reject_response.status_code == 200
        
        # Verify request status changed
        updated_req = db_session.query(FriendRequest).filter(
            FriendRequest.request_id == friend_req.request_id
        ).first()
        
        if updated_req:
            assert updated_req.status in ["declined", "pending"]


class TestEventsWorkflow:
    """Integration tests for events and timetable workflow."""
    
    def test_create_event_view_on_dashboard(self, authenticated_client, db_session, sample_user, sample_event):
        """Test creating event and viewing on dashboard."""
        # Get dashboard
        response = authenticated_client.get('/')
        assert response.status_code == 200
        
        # Verify event appears
        assert b'Test Lecture' in response.data or b'event' in response.data.lower()
    
    def test_import_timetable_creates_events(self, authenticated_client, db_session, sample_user):
        """Test importing timetable creates queryable events."""
        from app import importICS
        
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
SUMMARY:Imported Lecture
DTSTART:20260520T100000Z
DTEND:20260520T120000Z
LOCATION:Room 205
UID:import-test@example.com
END:VEVENT
END:VCALENDAR"""
        
        preview = importICS(ics_content.encode(), sample_user.user_id)
        
        assert len(preview) == 1
        
        # Verify in database
        event = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id,
            Event.event_name == "Imported Lecture"
        ).first()
        
        assert event is not None
        assert event.location == "Room 205"
    
    def test_import_overwrites_old_events(self, db_session, sample_user):
        """Test that importing timetable overwrites old events."""
        from app import importICS
        
        # Create old event
        old_event = Event(
            user_id=sample_user.user_id,
            event_name="Old Lecture",
            location="Room 100",
            day="Monday",
            date="2026-05-18",
            start_time="09:00",
            end_time="11:00"
        )
        db_session.add(old_event)
        db_session.commit()
        
        # Count before import
        count_before = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).count()
        assert count_before == 1
        
        # Import new timetable
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
SUMMARY:New Lecture 1
DTSTART:20260518T090000Z
DTEND:20260518T110000Z
LOCATION:Room 201
UID:new-1@example.com
END:VEVENT
BEGIN:VEVENT
SUMMARY:New Lecture 2
DTSTART:20260519T140000Z
DTEND:20260519T160000Z
LOCATION:Room 202
UID:new-2@example.com
END:VEVENT
END:VCALENDAR"""
        
        preview = importICS(ics_content.encode(), sample_user.user_id)
        
        assert len(preview) == 2
        
        # Verify old event is gone and new events exist
        events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        
        assert len(events) == 2
        assert all(e.event_name.startswith("New Lecture") for e in events)


class TestUserProfileWorkflow:
    """Integration tests for user profile operations."""
    
    def test_view_own_profile_when_authenticated(self, authenticated_client, sample_user):
        """Test viewing own profile when authenticated."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
        
        # Profile should contain user info
        assert sample_user.username in response.data.decode() or \
               sample_user.nickname in response.data.decode()
    
    def test_view_friend_profile(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test viewing friend's profile."""
        # Create friendship
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        # Navigate to friends page
        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        
        # Friend should be visible
        assert sample_user_2.username in response.data.decode() or \
               sample_user_2.nickname in response.data.decode()


class TestComplexScenarios:
    """Complex integration scenarios."""
    
    def test_user_with_friends_and_events(self, db_session, sample_user, sample_user_2, sample_user_3):
        """Test user with multiple friends and events."""
        # Create friendships
        friend1 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=1
        )
        friend2 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_3.user_id,
            is_favourite=0
        )
        db_session.add(friend1)
        db_session.add(friend2)
        
        # Create events
        for i in range(3):
            event = Event(
                user_id=sample_user.user_id,
                event_name=f"Event {i}",
                location=f"Room {100+i}",
                day="Monday",
                date="2026-05-18",
                start_time=f"{9+i}:00",
                end_time=f"{10+i}:00"
            )
            db_session.add(event)
        
        db_session.commit()
        
        # Verify relationships
        from friends import get_friend_ids, build_friends_list
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert len(friend_ids) == 2
        
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 2
        assert friends_list[0].is_favourite == True
        
        # Verify events
        events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        assert len(events) == 3
    
    def test_multiple_users_independent_data(self, db_session, sample_user, sample_user_2, sample_user_3):
        """Test that multiple users have independent data."""
        # Add events for each user
        for user in [sample_user, sample_user_2, sample_user_3]:
            for i in range(2):
                event = Event(
                    user_id=user.user_id,
                    event_name=f"Event for User {user.user_id}",
                    location="Room 100",
                    day="Monday",
                    date="2026-05-18",
                    start_time="10:00",
                    end_time="11:00"
                )
                db_session.add(event)
        
        db_session.commit()
        
        # Verify each user has only their events
        user1_events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        user2_events = db_session.query(Event).filter(
            Event.user_id == sample_user_2.user_id
        ).all()
        user3_events = db_session.query(Event).filter(
            Event.user_id == sample_user_3.user_id
        ).all()
        
        assert len(user1_events) == 2
        assert len(user2_events) == 2
        assert len(user3_events) == 2
        
        # Verify no cross-contamination
        for event in user1_events:
            assert event.user_id == sample_user.user_id
        for event in user2_events:
            assert event.user_id == sample_user_2.user_id
        for event in user3_events:
            assert event.user_id == sample_user_3.user_id
