from unittest.mock import patch


def test_contact_create_and_list(client, user1_auth_header):
    mock_contact = {
        "id": "c1111111-1111-1111-1111-111111111111",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "name": "Budi Santoso",
        "phone": "08123456789",
        "email": "budi@example.com",
        "address": "Jakarta",
        "notes": "Teman kantor"
    }

    with patch("app.repositories.contact.ContactRepository.find_by_name", return_value=None), \
         patch("app.repositories.contact.ContactRepository.create", return_value=mock_contact):
        res = client.post(
            "/api/v1/contacts",
            json={
                "name": "Budi Santoso",
                "phone": "08123456789",
                "email": "budi@example.com",
                "address": "Jakarta",
                "notes": "Teman kantor"
            },
            headers=user1_auth_header
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Budi Santoso"
