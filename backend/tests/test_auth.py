def test_unauthorized_access(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_me_endpoint_valid_token(client, user1_auth_header):
    res = client.get("/api/v1/auth/me", headers=user1_auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "user1@example.com"
