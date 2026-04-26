def test_index_redirect(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/signin" in response.location

def test_my_events_requires_login(client):
    response = client.get("/api/events/me")
    assert response.status_code == 401


def test_my_events_logged_in(logged_in_client):
    client, user = logged_in_client
    response = client.get('/')

    assert response.status_code == 200

def test_delete_event_not_found(logged_in_client):
    client, user = logged_in_client
    response = client.delete("/api/events/999999")
    assert response.status_code == 404