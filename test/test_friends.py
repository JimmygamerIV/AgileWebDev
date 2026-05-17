"""
Tests for friends functionality and friend requests.
Comprehensive testing for all friend-related features.
"""
import json
import pytest
from flask import session
from datetime import timedelta
from models import Friend, FriendRequest, User, Event
from database import Session
from friends import get_friend_ids, build_friends_list


class TestGetFriendIds:
    """Test the get_friend_ids function."""

    def test_get_friend_ids_no_friends(self, db_session, sample_user):
        """Test getting friend IDs when user has no friends."""
        friend_ids = get_friend_ids(db_session, sample_user.user_id)
        assert len(friend_ids) == 0

    def test_get_friend_ids_outgoing_friendship(self, db_session, sample_user, sample_user_2):
        """Test getting friend IDs with outgoing friendship."""
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
        friends_list = build_friends_list(db_session, sample_user.user_id)
        assert len(friends_list) == 0

    def test_build_friends_list_single_friend(self, db_session, sample_user, sample_user_2):
        """Test building friends list with single friend."""
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
        }, follow_redirects=False)
        # Unauthenticated users are redirected to signin
        assert response.status_code == 302

    def test_favourite_friend_missing_id(self, authenticated_client):
        """Test favourite friend with missing friend_id."""
        response = authenticated_client.post('/favourite_friend', data={})
        assert response.status_code == 400

    def test_favourite_friend_not_found(self, authenticated_client, sample_user_2):
        """Test favourite friend when friendship doesn't exist."""
        response = authenticated_client.post('/favourite_friend', data={
            'friend_id': sample_user_2.user_id
        })
        # Returns 404 if friend not found
        assert response.status_code in [404, 400]

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

        # Should return JSON response with 200
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data or 'is_favourite' in data

        # Verify in database
        db_session.expire_all()
        friend_row = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id
        ).first()
        if friend_row:
            assert friend_row.is_favourite == 1

    def test_favourite_friend_toggle_off(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Toggling favourite twice returns it to unfavourited."""
        friend = Friend(
            user_id=sample_user.user_id,
            friend_id=sample_user_2.user_id,
            is_favourite=1
        )
        db_session.add(friend)
        db_session.commit()

        response = authenticated_client.post('/favourite_friend', data={
            'friend_id': sample_user_2.user_id
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('is_favourite') is False


class TestAcceptFriendRequest:
    """Test accept friend request functionality."""

    def test_accept_friend_request_unauthenticated(self, client):
        """Test accepting friend request without authentication redirects."""
        response = client.post('/accept_request', data={'request_id': 1})
        # Flask-Login redirects unauthenticated users (302), not 401
        assert response.status_code == 302

    def test_accept_friend_request_invalid_id(self, authenticated_client):
        """Test accepting with missing sender_id returns 400."""
        response = authenticated_client.post('/accept_request', data={
            'request_id': 99999,
            'csrf_token': 'dummy'
        }, follow_redirects=True)

        assert response.status_code == 400

    def test_accept_friend_request_success(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Test accepting a valid pending friend request creates friendship."""
        req = FriendRequest(
            sender_id=sample_user_2.user_id,
            receiver_id=sample_user.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()

        response = authenticated_client.post('/accept_request', data={
            'request_id': req.request_id,
            'sender_id': sample_user_2.user_id,
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True

        # Verify bidirectional friendship was created
        db_session.expire_all()
        fwd = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id,
        ).first()
        rev = db_session.query(Friend).filter(
            Friend.user_id == sample_user_2.user_id,
            Friend.friend_id == sample_user.user_id,
        ).first()
        assert fwd is not None
        assert rev is not None

    def test_accept_nonexistent_request_returns_404(self, authenticated_client):
        """Accepting a request_id that doesn't exist returns 404."""
        response = authenticated_client.post('/accept_request', data={
            'request_id': 99999,
            'sender_id': 99999,
        })
        assert response.status_code == 404


class TestRejectFriendRequest:
    """Test reject friend request functionality."""

    def test_reject_friend_request_unauthenticated(self, client):
        """Test rejecting friend request without authentication redirects."""
        response = client.post('/reject_request', data={'request_id': 1})
        # Flask-Login redirects unauthenticated users (302), not 401
        assert response.status_code == 302

    def test_reject_friend_request_invalid_id(self, authenticated_client):
        """Test rejecting with a non-existent request_id returns 404."""
        response = authenticated_client.post('/reject_request', data={
            'request_id': 99999,
            'csrf_token': 'dummy'
        }, follow_redirects=True)

        assert response.status_code == 404

    def test_reject_friend_request_success(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Rejecting a pending request marks it as declined."""
        req = FriendRequest(
            sender_id=sample_user_2.user_id,
            receiver_id=sample_user.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()

        response = authenticated_client.post('/reject_request', data={
            'request_id': req.request_id,
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True

        db_session.expire_all()
        updated = db_session.query(FriendRequest).filter(
            FriendRequest.request_id == req.request_id
        ).first()
        assert updated.status == "declined"


class TestSearchUsers:
    """Test user search functionality."""

    def test_search_users_unauthenticated(self, client):
        """Search redirects unauthenticated requests."""
        response = client.get('/search_users?q=test')
        assert response.status_code == 302

    def test_search_users_short_query(self, authenticated_client):
        """Query shorter than 2 characters returns an empty list."""
        response = authenticated_client.get('/search_users?q=a')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_search_users_with_results(self, authenticated_client, sample_user_2):
        """Search returns matching users (excluding self)."""
        response = authenticated_client.get('/search_users?q=testuser2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert any(u['username'] == 'testuser2' for u in data)

    def test_search_users_excludes_self(self, authenticated_client, sample_user):
        """Search never returns the requesting user themselves."""
        response = authenticated_client.get(f'/search_users?q={sample_user.username}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(u['username'] != sample_user.username for u in data)

    def test_search_users_excludes_friends(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Users that are already friends are excluded from search results."""
        friend = Friend(user_id=sample_user.user_id, friend_id=sample_user_2.user_id)
        db_session.add(friend)
        db_session.commit()

        response = authenticated_client.get('/search_users?q=testuser2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(u['username'] != 'testuser2' for u in data)


class TestSendFriendRequest:
    """Test send friend request functionality."""

    def test_send_friend_request_unauthenticated(self, client, sample_user_2):
        """Sending a request while unauthenticated redirects."""
        response = client.post('/send_friend_request', data={
            'user_id': sample_user_2.user_id
        })
        assert response.status_code == 302

    def test_send_friend_request_to_self(self, authenticated_client, sample_user):
        """Sending a request to yourself returns 400."""
        response = authenticated_client.post('/send_friend_request', data={
            'user_id': sample_user.user_id
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'yourself' in data.get('error', '').lower()

    def test_send_friend_request_success(self, authenticated_client, db_session, sample_user_2):
        """Sending a valid friend request returns 200 with success=True."""
        response = authenticated_client.post('/send_friend_request', data={
            'user_id': sample_user_2.user_id
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True
        assert 'request_id' in data

    def test_send_friend_request_already_friends(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Sending a request to an existing friend returns 400."""
        friend = Friend(user_id=sample_user.user_id, friend_id=sample_user_2.user_id)
        db_session.add(friend)
        db_session.commit()

        response = authenticated_client.post('/send_friend_request', data={
            'user_id': sample_user_2.user_id
        })
        assert response.status_code == 400

    def test_send_friend_request_already_pending(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Sending a duplicate pending request returns 400."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()

        response = authenticated_client.post('/send_friend_request', data={
            'user_id': sample_user_2.user_id
        })
        assert response.status_code == 400

    def test_send_friend_request_by_username(self, authenticated_client, db_session, sample_user_2):
        """Friend request can be sent using the target's username."""
        response = authenticated_client.post('/send_friend_request', data={
            'username': sample_user_2.username
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True


class TestCancelFriendRequest:
    """Test cancel friend request functionality."""

    def test_cancel_request_unauthenticated(self, client):
        """Cancelling a request while unauthenticated redirects."""
        response = client.post('/cancel_request', data={'request_id': 1})
        assert response.status_code == 302

    def test_cancel_request_missing_id(self, authenticated_client):
        """Cancelling without a request_id returns 400."""
        response = authenticated_client.post('/cancel_request', data={})
        assert response.status_code == 400

    def test_cancel_request_success(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Cancelling a sent pending request removes it."""
        req = FriendRequest(
            sender_id=sample_user.user_id,
            receiver_id=sample_user_2.user_id,
            status="pending"
        )
        db_session.add(req)
        db_session.commit()
        # Cache the ID before the route deletes the row; accessing req.request_id
        # after deletion raises ObjectDeletedError.
        req_id = req.request_id

        response = authenticated_client.post('/cancel_request', data={
            'request_id': req_id
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True

        db_session.expire_all()
        gone = db_session.query(FriendRequest).filter(
            FriendRequest.request_id == req_id
        ).first()
        assert gone is None


class TestRemoveFriend:
    """Test remove friend functionality."""

    def test_remove_friend_unauthenticated(self, client, sample_user_2):
        """Removing a friend while unauthenticated redirects."""
        response = client.post('/remove_friend', data={
            'friend_id': sample_user_2.user_id
        })
        assert response.status_code == 302

    def test_remove_friend_missing_id(self, authenticated_client):
        """Removing a friend without friend_id returns 400."""
        response = authenticated_client.post('/remove_friend', data={})
        assert response.status_code == 400

    def test_remove_friend_success(self, authenticated_client, db_session, sample_user, sample_user_2):
        """Removing a friend deletes the friendship rows from both sides."""
        friend = Friend(user_id=sample_user.user_id, friend_id=sample_user_2.user_id)
        db_session.add(friend)
        db_session.commit()

        response = authenticated_client.post('/remove_friend', data={
            'friend_id': sample_user_2.user_id
        })
        # Route returns JSON 200 when Accept: application/json, otherwise redirects
        assert response.status_code in [200, 302]

        db_session.expire_all()
        fwd = db_session.query(Friend).filter(
            Friend.user_id == sample_user.user_id,
            Friend.friend_id == sample_user_2.user_id,
        ).first()
        assert fwd is None


class TestFriendsOnCampusAPI:
    """Test the /api/friends/on-campus endpoint."""

    def test_on_campus_unauthenticated(self, client):
        """Endpoint redirects unauthenticated requests."""
        response = client.get('/api/friends/on-campus')
        assert response.status_code == 302

    def test_on_campus_no_friends(self, authenticated_client):
        """Returns empty list when user has no friends."""
        response = authenticated_client.get('/api/friends/on-campus')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('on_campus') == []
