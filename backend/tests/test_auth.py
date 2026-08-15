import pytest
from app.models.user import User


def test_admin_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "Rajavel",
        "password": "Admin@123456"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["role"] == "ADMIN"


def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "Rajavel",
        "password": "WrongPassword123"
    })
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_login_nonexistent_user(client):
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "ghost_user",
        "password": "Password123!"
    })
    assert res.status_code == 401


def test_get_current_user_me(client, admin_headers):
    res = client.get("/api/v1/auth/me", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["username"] == "Rajavel"


def test_account_lockout_after_failures(client):
    # Attempt 5 failed logins to trigger lockout
    for _ in range(5):
        client.post("/api/v1/auth/login", json={
            "username_or_email": "manager",
            "password": "WrongPassword!"
        })
    
    # 6th attempt should be blocked with 403 Account Locked
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "manager",
        "password": "Manager@123456"
    })
    assert res.status_code == 403
    assert "locked" in res.json()["message"].lower()


def test_forgot_and_reset_password_flow(client, db_session):
    # Initiate forgot password
    res = client.post("/api/v1/auth/forgot-password", json={"email": "manager@example.com"})
    assert res.status_code == 200

    # Get reset token from DB
    manager = db_session.query(User).filter(User.email == "manager@example.com").first()
    assert manager.password_reset_token is not None

    # Reset password
    res = client.post("/api/v1/auth/reset-password", json={
        "token": manager.password_reset_token,
        "new_password": "NewManagerPassword@123"
    })
    assert res.status_code == 200

    # Test login with new password
    login_res = client.post("/api/v1/auth/login", json={
        "username_or_email": "manager",
        "password": "NewManagerPassword@123"
    })
    assert login_res.status_code == 200
