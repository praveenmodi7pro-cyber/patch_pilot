from app.auth import verify_token


def test_verify_token_valid():
    assert verify_token("tok_secret_123") is True


def test_verify_token_invalid():
    assert verify_token("bad_token") is False
    assert verify_token("") is False

