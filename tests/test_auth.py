"""
SatQuery AI - Auth Tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    # 1. Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "analyst@isro.gov.in",
            "password": "SecurePassword2026!",
            "full_name": "ISRO Remote Sensing Specialist"
        }
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "analyst@isro.gov.in"

    # 2. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "analyst@isro.gov.in",
            "password": "SecurePassword2026!"
        }
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    token = login_data["data"]["access_token"]
    assert token is not None

    # 3. Get /me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["success"] is True
    assert me_data["data"]["user"]["email"] == "analyst@isro.gov.in"
