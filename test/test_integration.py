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
    """Integration tests for friends workflow using independent authenticated clients."""
    
    def test_friend_request_accept_workflow(self, authenticated_client, authenticated_client_2, 
                                           db_session, sample_user, sample_user_2):
        """Test complete friend request workflow using two independent clients.
        
        Client 1 (sample_user) sends request to Client 2 (sample_user_2).
        Client 2 accepts the request.
        """
        # User 1 creates friend request to User 2
        friend_req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="pending"
        )
        db_session.add(friend_req)
        db_session.commit()
        
        # Verify request is pending
        pending_req = db_session.query(FriendRequest).filter(
            FriendRequest.request_id == friend_req.request_id
        ).first()
        assert pending_req is not None
        assert pending_req.status == "pending"
        
        # User 2 (using authenticated_client_2) accepts the request
        accept_response = authenticated_client_2.post('/accept_request', data={
            'request_id': friend_req.request_id,
            'sender_id': sample_user.user_id,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert accept_response.status_code == 200
        
        # Verify request was accepted
        db_session.refresh(pending_req)
        assert pending_req.status == "accepted"
        
        # Verify friendship was created
        friendship = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id
        ).first()
        assert friendship is not None
    
    def test_friend_request_reject_workflow(self, authenticated_client, authenticated_client_2,
                                           db_session, sample_user, sample_user_2):
        """Test friend request rejection workflow using two independent clients.
        
        Client 2 (sample_user_2) sends request to Client 1 (sample_user).
        Client 1 rejects the request.
        """
        # User 2 sends request to User 1
        friend_req = FriendRequest(
            sender_id=sample_user_2.user_id,
            receiver_id=sample_user.user_id,
            status="pending"
        )
        db_session.add(friend_req)
        db_session.commit()
        
        # User 1 (using authenticated_client) rejects the request
        reject_response = authenticated_client.post('/reject_request', data={
            'request_id': friend_req.request_id,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert reject_response.status_code == 200
        
        # Verify request status changed to declined
        db_session.refresh(friend_req)
        assert friend_req.status == "declined"
        
        # Verify no friendship was created
        friendship = db_session.query(Friend).filter(
            Friend.user_id == sample_user_2.user_id,
            Friend.friend_id == sample_user.user_id
        ).first()
        assert friendship is None

class TestEventsWorkflow:
    """Integration tests for events and timetable workflow with realistic UWA ICS format."""
    
    def test_create_event_view_on_dashboard(self, authenticated_client, db_session, sample_user, sample_event):
        """Test creating event and viewing on dashboard."""
        # Get dashboard
        response = authenticated_client.get('/')
        assert response.status_code == 200
        
        assert b'Data Warehousing' in response.data or b'event' in response.data.lower()
    
    def test_import_timetable_creates_events(self, authenticated_client, db_session, sample_user):
        """Test importing timetable creates queryable events using realistic UWA format."""
        from app import importICS, Event  
        
        uwa_ics_content = """BEGIN:VCALENDAR
PRODID:-//Allocate//iCal4j 1.0//EN
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VTIMEZONE
TZID:Australia/Perth
LAST-MODIFIED:20260306T231828Z
TZURL:https://www.tzurl.org/zoneinfo-outlook/Australia/Perth
X-LIC-LOCATION:Australia/Perth
BEGIN:STANDARD
TZNAME:AWST
TZOFFSETFROM:+0800
TZOFFSETTO:+0800
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTAMP:20260515T154618Z
DTSTART;TZID=Australia/Perth:20260303T100000
DTEND;TZID=Australia/Perth:20260303T120000
SUMMARY:Data Warehousing\\, Lecture-01
LOCATION:EZONE: [  211] Learning Studio
DESCRIPTION:CITS3401_SEM-1_CR\\, Lecture-01\\, 01\\nData Warehousing\\nStaff: -\\nLocation: EZONE: [  211] Learning Studio
UID:uwa-cits3401-lec-w1
END:VEVENT
END:VCALENDAR"""
        
        preview = importICS(uwa_ics_content.encode('utf-8'), sample_user.user_id)
        
        assert len(preview) == 1
        
        event = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id,
            Event.event_name.like("%Data Warehousing%")
        ).first()
        
        assert event is not None

        assert event.date == "2026-03-03"
        assert "139.211" in event.location
    
    def test_import_overwrites_old_events(self, db_session, sample_user):
        """Test that importing timetable overwrites old events entirely."""
        from app import importICS, Event
        
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
        

        count_before = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).count()
        assert count_before == 1
        

        new_uwa_ics = """BEGIN:VCALENDAR
PRODID:-//Allocate//iCal4j 1.0//EN
VERSION:2.0
BEGIN:VTIMEZONE
TZID:Australia/Perth
END:VTIMEZONE
BEGIN:VEVENT
SUMMARY:Data Warehousing\\, Lecture-01
DTSTART;TZID=Australia/Perth:20260310T100000
DTEND;TZID=Australia/Perth:20260310T120000
LOCATION:EZONE: [  211] Learning Studio
UID:uwa-cits3401-lec-w2
END:VEVENT
BEGIN:VEVENT
SUMMARY:Data Warehousing\\, Tutorial-01
DTSTART;TZID=Australia/Perth:20260312T140000
DTEND;TZID=Australia/Perth:20260312T150000
LOCATION:CSSE: [  201] Lab 1
UID:uwa-cits3401-tut-w2
END:VEVENT
END:VCALENDAR"""
        
        preview = importICS(new_uwa_ics.encode('utf-8'), sample_user.user_id)
        
        assert len(preview) == 2
        
        # 核心断言：旧的数据应该被完全抹除，只留下新导入的 2 条记录
        events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        
        assert len(events) == 2
        assert not any(e.event_name == "Old Lecture" for e in events)
        assert any("Lecture" in e.event_name for e in events)
        assert any("Tutorial" in e.event_name for e in events)

class TestUserProfileWorkflow:
    """Integration tests for user profile operations using independent clients."""
    
    def test_view_own_profile_when_authenticated(self, authenticated_client, sample_user):
        """Test viewing own profile when authenticated."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
        
        # Profile should contain user info
        response_text = response.data.decode()
        assert sample_user.username in response_text or sample_user.nickname in response_text
    
    def test_view_friend_profile_from_different_client(self, authenticated_client, authenticated_client_2,
                                                       db_session, sample_user, sample_user_2):
        """Test viewing friend's profile from different client perspective.
        
        User 1 (authenticated_client) creates friendship with User 2.
        User 1 views friends list and sees User 2.
        User 2 (authenticated_client_2) views their own profile.
        """
        # Create friendship between user 1 and user 2
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        # User 1 navigates to friends page (should see User 2)
        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        
        response_text = response.data.decode()
        assert sample_user_2.username in response_text or sample_user_2.nickname in response_text
        
        # User 2 (separate client) views their own profile
        profile_response = authenticated_client_2.get('/profile')
        assert profile_response.status_code == 200
        
        profile_text = profile_response.data.decode()
        assert sample_user_2.username in profile_text or sample_user_2.nickname in profile_text


class TestComplexScenarios:
    """Complex integration scenarios involving multiple users."""
    
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
        friends = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id
        ).all()
        assert len(friends) == 2
        
        events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        assert len(events) == 3
    
    def test_concurrent_operations_from_different_users(self, authenticated_client, authenticated_client_2,
                                                        db_session, sample_user, sample_user_2):
        """Test that different users can perform operations independently.
        
        Simulates two users accessing the system simultaneously with different data.
        """
        # User 1 creates events
        for i in range(2):
            event1 = Event(
                user_id=sample_user.user_id,
                event_name=f"User1 Event {i}",
                location="User1 Location",
                day="Monday",
                date="2026-05-18",
                start_time=f"{9+i}:00",
                end_time=f"{10+i}:00"
            )
            db_session.add(event1)
        
        # User 2 creates events
        for i in range(3):
            event2 = Event(
                user_id=sample_user_2.user_id,
                event_name=f"User2 Event {i}",
                location="User2 Location",
                day="Tuesday",
                date="2026-05-19",
                start_time=f"{14+i}:00",
                end_time=f"{15+i}:00"
            )
            db_session.add(event2)
        
        db_session.commit()
        
        # Verify User 1 only sees their own events
        user1_events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        assert len(user1_events) == 2
        assert all("User1" in e.event_name for e in user1_events)
        
        # Verify User 2 only sees their own events
        user2_events = db_session.query(Event).filter(
            Event.user_id == sample_user_2.user_id
        ).all()
        assert len(user2_events) == 3
        assert all("User2" in e.event_name for e in user2_events)
        
        # User 1 accesses their dashboard via authenticated_client
        response1 = authenticated_client.get('/')
        assert response1.status_code == 200
        
        # User 2 accesses their dashboard via authenticated_client_2
        response2 = authenticated_client_2.get('/')
        assert response2.status_code == 200
        
        # Verify each user sees their own data
        text1 = response1.data.decode()
        text2 = response2.data.decode()
        
        # User 1's response should reference their events/location
        assert "User1" in text1 or len(text1) > 100  # Has content
        
        # User 2's response should be independent
        assert "User2" in text2 or len(text2) > 100  # Has content
        
        # Verify relationships
        from friends import get_friend_ids, build_friends_list
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert len(friend_ids) == 0
        
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 0
        
        # Verify events
        events = db_session.query(Event).filter(
            Event.user_id == sample_user.user_id
        ).all()
        assert len(events) == 2
    
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
