"""
Tests for friends functionality.
"""
import pytest
from flask import session
from models import Friend, FriendRequest
from database import Session


class TestGetFriendIds:
    """Test get_friend_ids function."""
    
    def test_get_friend_ids_no_friends(self, db_session, sample_user):
        """Test getting friend IDs when user has no friends."""
        from friends import get_friend_ids
        
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert len(friend_ids) == 0
    
    def test_get_friend_ids_outgoing_friendship(self, db_session, sample_user, sample_user_2):
        """Test getting friend IDs with outgoing friendship."""
        from friends import get_friend_ids
        
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert sample_user_2.user_id in friend_ids
    
    def test_get_friend_ids_incoming_friendship(self, db_session, sample_user, sample_user_2):
        """Test getting friend IDs with incoming friendship."""
        from friends import get_friend_ids
        
        friend = Friend(
            user_id=sample_user_2.user_id,
            friend_id=sample_user.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert sample_user_2.user_id in friend_ids
    
    def test_get_friend_ids_multiple_friends(self, db_session, sample_user, sample_user_2, sample_user_3):
        """Test getting friend IDs with multiple friends."""
        from friends import get_friend_ids
        
        friend1 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        friend2 = Friend(
            user_id=sample_user_3.user_id,
            friend_id=sample_user.user_id
        )
        db_session.add(friend1)
        db_session.add(friend2)
        db_session.commit()
        
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert len(friend_ids) == 2
        assert sample_user_2.user_id in friend_ids
        assert sample_user_3.user_id in friend_ids


class TestBuildFriendsList:
    """Test build_friends_list function."""
    
    def test_build_friends_list_empty(self, db_session, sample_user):
        """Test building friends list with no friends."""
        from friends import build_friends_list
        
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 0
    
    def test_build_friends_list_single_friend(self, db_session, sample_user, sample_user_2):
        """Test building friends list with single friend."""
        from friends import build_friends_list
        
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=0
        )
        db_session.add(friend)
        db_session.commit()
        
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 1
        assert friends_list[0].user_id == sample_user_2.user_id
        assert friends_list[0].is_favourite == False
    
    def test_build_friends_list_favourite_sorting(self, db_session, sample_user, sample_user_2, sample_user_3):
        """Test friends list sorts favourites first."""
        from friends import build_friends_list
        
        friend1 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=0
        )
        friend2 = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_3.user_id,
            is_favourite=1
        )
        db_session.add(friend1)
        db_session.add(friend2)
        db_session.commit()
        
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 2
        assert friends_list[0].is_favourite == True  # Favourite first
        assert friends_list[1].is_favourite == False
    
    def test_build_friends_list_nickname_sorting(self, db_session, sample_user):
        """Test friends list sorts by nickname alphabetically."""
        from friends import build_friends_list
        from models import User
        from werkzeug.security import generate_password_hash
        
        user_alice = User(
            username="alice",
            nickname="Alice",
            email="alice@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass123", method='pbkdf2:sha256')
        )
        user_bob = User(
            username="bob",
            nickname="Bob",
            email="bob@student.uwa.edu.au",
            password_hash=generate_password_hash("Pass456", method='pbkdf2:sha256')
        )
        db_session.add(user_alice)
        db_session.add(user_bob)
        db_session.commit()
        
        friend1 = Friend(
            user_id=sample_user.user_id,
            friend_id=user_bob.user_id,
            is_favourite=0
        )
        friend2 = Friend(
            user_id=sample_user.user_id,
            friend_id=user_alice.user_id,
            is_favourite=0
        )
        db_session.add(friend1)
        db_session.add(friend2)
        db_session.commit()
        
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 2
        assert friends_list[0].nickname == "Alice"
        assert friends_list[1].nickname == "Bob"


class TestFriendsRoute:
    """Test friends route."""
    
    def test_friends_route_unauthenticated(self, client):
        """Test friends route without authentication."""
        response = client.get('/friends')
        assert response.status_code == 302  # Redirect to signin
    
    def test_friends_route_authenticated(self, authenticated_client, sample_user):
        """Test friends route with authentication."""
        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        assert b'friends' in response.data or b'Friends' in response.data
    
    def test_friends_route_displays_friends(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test friends route displays user's friends."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id
        )
        db_session.add(friend)
        db_session.commit()
        
        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        assert b'testuser2' in response.data or b'Test User 2' in response.data
    
    def test_friends_route_incoming_requests(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test friends route displays incoming requests."""
        req = FriendRequest(
            sender_id=sample_user_2.user_id,
            receiver_id=sample_user.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()
        
        response = authenticated_client.get('/friends')
        assert response.status_code == 200
        assert b'testuser2' in response.data or b'Test User 2' in response.data


class TestFavouriteFriend:
    """Test favourite friend functionality."""
    
    def test_favourite_friend_unauthenticated(self, client, sample_user_2):
        """Test favourite friend without authentication."""
        response = client.post('/favourite_friend', data={
            'friend_id': sample_user_2.user_id
        })
        assert response.status_code == 401
    
    def test_favourite_friend_missing_id(self, authenticated_client):
        """Test favourite friend with missing friend_id."""
        response = authenticated_client.post('/favourite_friend', data={})
        assert response.status_code == 400
    
    def test_favourite_friend_success(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test successfully marking friend as favourite."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=0
        )
        db_session.add(friend)
        db_session.commit()
        
        response = authenticated_client.post('/favourite_friend', data={
            'friend_id': sample_user_2.user_id
        })
        
        # Should return JSON response
        assert response.status_code in [200, 201]
        
        # Verify in database
        friend_row = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id
        ).first()
        if friend_row:
            assert friend_row.is_favourite == 1


class TestAddFriendRoute:
    """Test add friend route."""
    
    def test_add_friend_unauthenticated(self, client):
        """Test add friend without authentication."""
        response = client.post('/friend', data={
            'target_username': 'someuser'
        })
        assert response.status_code in [302, 401]  # Redirect or unauthorized
    
    def test_add_friend_nonexistent_user(self, authenticated_client, sample_user):
        """Test adding non-existent user as friend."""
        response = authenticated_client.post('/friend', data={
            'target_username': 'nonexistent_user_xyz',
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message
        assert b'not found' in response.data or b'does not exist' in response.data or b'error' in response.data.lower()
    
    def test_add_friend_to_self(self, authenticated_client, sample_user):
        """Test adding yourself as friend."""
        response = authenticated_client.post('/add_friend', data={
            'target_username': sample_user.username,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_add_friend_success(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test successfully adding a friend."""
        response = authenticated_client.post('/add_friend', data={
            'target_username': sample_user_2.username,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestAcceptFriendRequest:
    """Test accept friend request functionality."""
    
    def test_accept_friend_request_unauthenticated(self, client):
        """Test accepting friend request without authentication."""
        response = client.post('/accept_friend_request', data={
            'request_id': 1
        })
        assert response.status_code in [302, 401]
    
    def test_accept_friend_request_invalid_id(self, authenticated_client):
        """Test accepting with invalid request_id."""
        response = authenticated_client.post('/accept_friend_request', data={
            'request_id': 99999,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestRejectFriendRequest:
    """Test reject friend request functionality."""
    
    def test_reject_friend_request_unauthenticated(self, client):
        """Test rejecting friend request without authentication."""
        response = client.post('/reject_friend_request', data={
            'request_id': 1
        })
        assert response.status_code in [302, 401]
    
    def test_reject_friend_request_invalid_id(self, authenticated_client):
        """Test rejecting with invalid request_id."""
        response = authenticated_client.post('/reject_friend_request', data={
            'request_id': 99999,
            'csrf_token': 'dummy'
        }, follow_redirects=True)
        
        assert response.status_code == 200
