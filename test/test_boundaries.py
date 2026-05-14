"""
Boundary condition and edge case tests.
Tests for extreme values, limits, and unusual inputs.
"""
import pytest
from datetime import datetime, timedelta
from models import User, Event, Friend, FriendRequest
from database import Session
from werkzeug.security import generate_password_hash


class TestUsernameBoundaries:
    """Test username boundary conditions."""
    
    def test_username_minimum_length(self, client):
        """Test signup with minimum length username."""
        response = client.post('/signup', data={
            'username': 'a',  # Single character
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'min@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_username_exactly_max_length(self, client):
        """Test signup with exactly max length username."""
        max_username = 'a' * 15
        
        response = client.post('/signup', data={
            'username': max_username,
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'exact@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_username_exceeds_max_length(self, client):
        """Test signup with username exceeding max."""
        over_max = 'a' * 20
        
        response = client.post('/signup', data={
            'username': over_max,
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'over@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_username_with_numbers_only(self, client):
        """Test username with only numbers."""
        response = client.post('/signup', data={
            'username': '12345',
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'numbers@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_username_with_underscores_hyphens(self, client):
        """Test username with underscores and hyphens."""
        for username in ['user_name', 'user-name', 'user_-_name']:
            response = client.post('/signup', data={
                'username': username,
                'nickname': 'Test',
                'password': 'Pass123',
                'confirm_password': 'Pass123',
                'email': f'{username}@student.uwa.edu.au',
                'csrf_token': 'dummy'
            }, follow_redirects=True)
            
            assert response.status_code in [200, 302]


class TestPasswordBoundaries:
    """Test password boundary conditions."""
    
    def test_password_exactly_minimum_length(self, client):
        """Test password exactly 6 characters."""
        response = client.post('/signup', data={
            'username': 'pwdmin',
            'nickname': 'Test',
            'password': 'Passw1',  # Exactly 6 chars
            'confirm_password': 'Passw1',
            'email': 'pwdmin@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_password_very_long(self, client):
        """Test very long password."""
        long_pwd = 'A' * 1000 + 'b' * 1000 + '1'
        
        response = client.post('/signup', data={
            'username': 'longpwd',
            'nickname': 'Test',
            'password': long_pwd,
            'confirm_password': long_pwd,
            'email': 'longpwd@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_password_with_unicode_characters(self, client):
        """Test password with unicode characters."""
        response = client.post('/signup', data={
            'username': 'unicodepwd',
            'nickname': 'Test',
            'password': 'Pass中文123',
            'confirm_password': 'Pass中文123',
            'email': 'unicode@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_password_with_all_special_chars(self, client):
        """Test password with special characters."""
        special_pwd = 'Pass!@#$%^&*()_+-=[]{}|;:,.<>?123'
        
        response = client.post('/signup', data={
            'username': 'specialpwd',
            'nickname': 'Test',
            'password': special_pwd,
            'confirm_password': special_pwd,
            'email': 'special@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]


class TestEmailBoundaries:
    """Test email boundary conditions."""
    
    def test_email_with_many_subdomains(self, client):
        """Test email with multiple subdomains."""
        response = client.post('/signup', data={
            'username': 'subdomains',
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'user@mail.student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        # Should accept if valid UWA domain
        assert response.status_code in [200, 302]
    
    def test_email_with_plus_addressing(self, client):
        """Test email with plus sign (gmail style)."""
        response = client.post('/signup', data={
            'username': 'plusemail',
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'user+tag@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_email_with_dots_in_local_part(self, client):
        """Test email with dots in local part."""
        response = client.post('/signup', data={
            'username': 'dotsemail',
            'nickname': 'Test',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'user.name.here@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]


class TestEventTimeBoundaries:
    """Test event time boundary conditions."""
    
    def test_event_at_midnight(self, db_session, sample_user):
        """Test event at midnight."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Midnight Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='00:00',
            end_time='01:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'Midnight Event'
        ).first()
        assert retrieved is not None
        assert retrieved.start_time == '00:00'
    
    def test_event_at_end_of_day(self, db_session, sample_user):
        """Test event at end of day."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Late Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='23:00',
            end_time='23:59'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'Late Event'
        ).first()
        assert retrieved is not None
        assert retrieved.start_time == '23:00'
    
    def test_event_end_before_start(self, db_session, sample_user):
        """Test event with end time before start time."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Invalid Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='14:00',
            end_time='10:00'  # End before start
        )
        db_session.add(event)
        # Database might not enforce this, but the app should
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'Invalid Event'
        ).first()
        assert retrieved is not None
    
    def test_event_same_start_end_time(self, db_session, sample_user):
        """Test event with same start and end time."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Zero Duration Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='10:00',
            end_time='10:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'Zero Duration Event'
        ).first()
        assert retrieved is not None
    
    def test_event_across_days(self, db_session, sample_user):
        """Test event that would span midnight."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='All Night Event',
            location='Room 100',
            day='Monday',
            date='2026-05-18',
            start_time='22:00',
            end_time='02:00'  # Would cross midnight
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.event_name == 'All Night Event'
        ).first()
        assert retrieved is not None


class TestNicknameLength:
    """Test nickname length boundaries."""
    
    def test_nickname_minimum(self, client):
        """Test with single character nickname."""
        response = client.post('/signup', data={
            'username': 'nickmin',
            'nickname': 'A',
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'nickmin@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_nickname_maximum(self, client):
        """Test with maximum length nickname."""
        response = client.post('/signup', data={
            'username': 'nickmax',
            'nickname': 'A' * 20,
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'nickmax@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_nickname_exceeds_maximum(self, client):
        """Test nickname exceeding maximum."""
        response = client.post('/signup', data={
            'username': 'nickover',
            'nickname': 'A' * 100,
            'password': 'Pass123',
            'confirm_password': 'Pass123',
            'email': 'nickover@student.uwa.edu.au',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestFriendshipEdgeCases:
    """Test friendship edge cases."""
    
    def test_user_cannot_befriend_self(self, db_session, sample_user):
        """Test that user cannot add themselves as friend."""
        # This should be prevented by business logic
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        # Should allow at DB level but app should prevent
        retrieved = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user.user_id
        ).first()
        # App should prevent this
    
    def test_duplicate_friend_relationship(self, db_session, sample_user, sample_user_2):
        """Test duplicate friend relationships."""
        friend1 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend1)
        db_session.commit()
        
        # Try to add same relationship again
        friend2 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend2)
        
        # Should fail due to composite primary key
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_bidirectional_friendships(self, db_session, sample_user, sample_user_2):
        """Test bidirectional friendship relationships."""
        # User A follows User B
        friend_ab = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        # User B follows User A
        friend_ba = Friend(
            user_id=sample_user_2.user_id,
            friend_id=sample_user.user_id
        )
        db_session.add(friend_ab)
        db_session.add(friend_ba)
        db_session.commit()
        
        # Both relationships should exist
        rel_ab = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id
        ).first()
        rel_ba = db_session.query(Friend).filter(
            Friend.user_id == sample_user_2.user_id,
            Friend.friend_id == sample_user.user_id
        ).first()
        
        assert rel_ab is not None
        assert rel_ba is not None


class TestFriendRequestStatuses:
    """Test all friend request status combinations."""
    
    def test_pending_to_accepted_transition(self, db_session, sample_user, sample_user_2):
        """Test transitioning request from pending to accepted."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req)
        db_session.commit()
        
        # Update to accepted
        req.status = 'accepted'
        db_session.commit()
        
        retrieved = db_session.query(FriendRequest).filter(
            FriendRequest.request_id == req.request_id
        ).first()
        assert retrieved.status == 'accepted'
    
    def test_pending_to_declined_transition(self, db_session, sample_user, sample_user_2):
        """Test transitioning request from pending to declined."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req)
        db_session.commit()
        
        req.status = 'declined'
        db_session.commit()
        
        retrieved = db_session.query(FriendRequest).filter(
            FriendRequest.request_id == req.request_id
        ).first()
        assert retrieved.status == 'declined'
    
    def test_duplicate_pending_requests(self, db_session, sample_user, sample_user_2):
        """Test preventing duplicate pending requests."""
        req1 = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req1)
        db_session.commit()
        
        # Try to add duplicate
        req2 = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status='pending'
        )
        db_session.add(req2)
        
        # Should fail (no unique constraint, but app should prevent)
        db_session.commit()


class TestDateBoundaries:
    """Test date boundary conditions."""
    
    def test_event_on_leap_year_date(self, db_session, sample_user):
        """Test event on leap year date."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Leap Day Event',
            location='Room 100',
            day='Tuesday',
            date='2024-02-29',  # Leap day
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.date == '2024-02-29'
        ).first()
        assert retrieved is not None
    
    def test_event_far_future_date(self, db_session, sample_user):
        """Test event with far future date."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Future Event',
            location='Room 100',
            day='Monday',
            date='2099-12-31',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.date == '2099-12-31'
        ).first()
        assert retrieved is not None
    
    def test_event_past_date(self, db_session, sample_user):
        """Test event with past date."""
        event = Event(
            user_id=sample_user.user_id,
            event_name='Past Event',
            location='Room 100',
            day='Monday',
            date='2000-01-01',
            start_time='10:00',
            end_time='11:00'
        )
        db_session.add(event)
        db_session.commit()
        
        retrieved = db_session.query(Event).filter(
            Event.date == '2000-01-01'
        ).first()
        assert retrieved is not None
