from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)


def test_password_hash_round_trip_and_rejects_invalid_password():
    password_hash = hash_password("correct horse battery staple")

    assert "correct horse battery staple" not in password_hash
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("incorrect", password_hash)


def test_password_verification_rejects_malformed_hash():
    assert not verify_password("password", "not-a-valid-hash")


def test_session_tokens_are_random_and_stored_as_digests():
    first_token = generate_session_token()
    second_token = generate_session_token()

    assert first_token != second_token
    assert hash_session_token(first_token) != first_token
    assert hash_session_token(first_token) == hash_session_token(first_token)
