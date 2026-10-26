import pytest
from pydantic import ValidationError

from app.api.auth import UserRegister, _validate_password_strength


def test_registration_normalizes_email():
    payload = UserRegister(
        email=" Learner@Example.COM ",
        password="Strong123",
        full_name="Learner",
        display_name="Learner",
    )
    assert payload.email == "learner@example.com"


def test_registration_rejects_invalid_age():
    with pytest.raises(ValidationError):
        UserRegister(
            email="learner@example.com",
            password="Strong123",
            full_name="Learner",
            display_name="Learner",
            age=3,
        )


def test_password_rejects_bcrypt_truncation():
    with pytest.raises(ValueError):
        _validate_password_strength("A1" + "x" * 80)
