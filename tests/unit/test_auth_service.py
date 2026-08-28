import pytest
from app.core.security import hash_password, verify_password, create_access_token, verify_token

def test_hash_and_verify():
    h = hash_password("Test1234")
    assert verify_password("Test1234", h)
    assert not verify_password("Wrong123", h)

def test_jwt_create_verify():
    tok = create_access_token("test-user-id", "FIELD_TECH")
    payload = verify_token(tok)
    assert payload["user_id"] == "test-user-id"
    assert payload["role"] == "FIELD_TECH"
    assert "exp" in payload

def test_jwt_invalid():
    with pytest.raises(ValueError):
        verify_token("invalid.token.here")
