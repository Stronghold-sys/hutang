import pytest
import jwt
import sys
import os
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

USER_ID_1 = "00000000-0000-0000-0000-000000000001"
USER_ID_2 = "00000000-0000-0000-0000-000000000002"


def generate_mock_jwt(user_id: str, email: str = "test@example.com", role: str = "user") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated"
    }
    return jwt.encode(payload, "secret-key", algorithm="HS256")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user1_auth_header():
    token = generate_mock_jwt(USER_ID_1, "user1@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user2_auth_header():
    token = generate_mock_jwt(USER_ID_2, "user2@example.com")
    return {"Authorization": f"Bearer {token}"}
