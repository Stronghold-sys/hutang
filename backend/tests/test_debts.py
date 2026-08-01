from unittest.mock import patch


def test_create_debt_validation(client, user1_auth_header):
    # Invalid negative principal
    res = client.post(
        "/api/v1/debts",
        json={
            "contact_name": "Rian Saputra",
            "type": "receivable",
            "principal_amount": -1000
        },
        headers=user1_auth_header
    )
    assert res.status_code == 422


def test_create_debt_success(client, user1_auth_header):
    mock_debt = {
        "id": "d1111111-1111-1111-1111-111111111111",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "contact_id": "c1111111-1111-1111-1111-111111111111",
        "type": "receivable",
        "title": "Pinjaman motor",
        "principal_amount": 500000,
        "paid_amount": 0,
        "remaining_amount": 500000,
        "status": "active",
        "transaction_date": "2026-07-28",
        "due_date": "2026-08-10",
        "currency": "IDR",
        "interest_type": "none",
        "interest_value": 0,
        "late_fee": 0,
        "reminder_enabled": False
    }

    with patch("app.services.debt.DebtService.create_debt", return_value=mock_debt):
        res = client.post(
            "/api/v1/debts",
            json={
                "contact_name": "Rian Saputra",
                "type": "receivable",
                "principal_amount": 500000,
                "title": "Pinjaman motor",
                "due_date": "2026-08-10"
            },
            headers=user1_auth_header
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["remaining_amount"] == 500000
