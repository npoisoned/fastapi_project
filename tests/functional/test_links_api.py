def register_user(client, email="user@example.com", password="12345678"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )


def login_user(client, email="user@example.com", password="12345678"):
    return client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )


def get_auth_headers(client, email="user@example.com", password="12345678"):
    register_user(client, email=email, password=password)
    login_response = login_user(client, email=email, password=password)
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_link_without_auth(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "python-link",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "python-link"
    assert data["original_url"] == "https://www.python.org/"
    assert data["created_by_authenticated"] is False
    assert data["user_id"] is None


def test_create_link_with_auth(client):
    headers = get_auth_headers(client)

    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "python-auth-link",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "python-auth-link"
    assert data["created_by_authenticated"] is True
    assert data["user_id"] is not None


def test_create_link_duplicate_alias(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "duplicate-link",
        },
    )

    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://docs.python.org",
            "custom_alias": "duplicate-link",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Alias already exists"


def test_create_link_invalid_url(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "not-a-url",
            "custom_alias": "bad-url-link",
        },
    )

    assert response.status_code == 422


def test_create_link_reserved_alias(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "health",
        },
    )

    assert response.status_code == 422


def test_get_link_info(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "info-link",
        },
    )

    response = client.get("/links/info-link")

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "info-link"
    assert data["original_url"] == "https://www.python.org/"


def test_search_link_by_original_url(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "search-link",
        },
    )

    response = client.get("/links/search", params={"original_url": "https://www.python.org/"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["short_code"] == "search-link"


def test_redirect_to_original(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "redirect-link",
        },
    )

    response = client.get("/redirect-link", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://www.python.org/"


def test_get_link_stats_after_redirect(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "stats-link",
        },
    )

    client.get("/stats-link", follow_redirects=False)

    response = client.get("/links/stats-link/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["click_count"] == 1
    assert data["last_accessed_at"] is not None


def test_update_own_link(client):
    headers = get_auth_headers(client)

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "update-link",
        },
        headers=headers,
    )

    response = client.put(
        "/links/update-link",
        json={"original_url": "https://docs.python.org"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://docs.python.org/"


def test_update_link_without_auth(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "no-auth-update",
        },
    )

    response = client.put(
        "/links/no-auth-update",
        json={"original_url": "https://docs.python.org"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_update_other_user_link_forbidden(client):
    owner_headers = get_auth_headers(client, email="owner@example.com")
    other_headers = get_auth_headers(client, email="other@example.com")

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "foreign-link",
        },
        headers=owner_headers,
    )

    response = client.put(
        "/links/foreign-link",
        json={"original_url": "https://docs.python.org"},
        headers=other_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You can update only your own links"


def test_delete_own_link(client):
    headers = get_auth_headers(client)

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "delete-link",
        },
        headers=headers,
    )

    response = client.delete("/links/delete-link", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Link deleted successfully"

    check_response = client.get("/links/delete-link")
    assert check_response.status_code == 404


def test_delete_other_user_link_forbidden(client):
    owner_headers = get_auth_headers(client, email="owner2@example.com")
    other_headers = get_auth_headers(client, email="other2@example.com")

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://www.python.org",
            "custom_alias": "foreign-delete-link",
        },
        headers=owner_headers,
    )

    response = client.delete("/links/foreign-delete-link", headers=other_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "You can delete only your own links"


def test_get_missing_link_info_returns_404(client):
    response = client.get("/links/missing-link")
    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


def test_get_missing_stats_returns_404(client):
    response = client.get("/links/missing-link/stats")
    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


def test_get_expired_links_history_endpoint(client):
    response = client.get("/links/expired/history")
    assert response.status_code == 200
    assert response.json() == []


def test_update_missing_link_returns_404(client):
    headers = get_auth_headers(client)

    response = client.put(
        "/links/missing-link",
        json={"original_url": "https://docs.python.org"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


def test_delete_missing_link_returns_404(client):
    headers = get_auth_headers(client)

    response = client.delete("/links/missing-link", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"
