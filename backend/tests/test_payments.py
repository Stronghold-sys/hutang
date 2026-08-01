from unittest.mock import patch
from decimal import Decimal


def test_payment_overpayment_validation(client, user1_auth_header):
    mock_debt = {
        "id": "d1111111-1111-1111-1111-111111111111",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "principal_amount": 500000,
        "paid_amount": 0,
        "remaining_amount": 500000,
        "status": "active"
    }

    with patch("app.services.debt.DebtService.get_debt_by_id", return_value=mock_debt):
        res = client.post(
            "/api/v1/debts/d1111111-1111-1111-1111-111111111111/payments",
            json={
                "amount": 600000
            },
            headers=user1_auth_header
        )
        assert res.status_code == 422 or res.status_code == 400
        assert res.json()["success"] is False
