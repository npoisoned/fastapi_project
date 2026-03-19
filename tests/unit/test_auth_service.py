from app.models.user import User
from app.services.auth_service import auth_service
from app.core.security import verify_password


def test_register_user_success(db):
    user = auth_service.register_user(
        db,
        email="unit@example.com",
        password="12345678",
    )

    assert user.id is not None
    assert user.email == "unit@example.com"
    assert user.password_hash != "12345678"
    assert verify_password("12345678", user.password_hash) is True


def test_register_user_duplicate_email(db):
    auth_service.register_user(
        db,
        email="unit@example.com",
        password="12345678",
    )

    try:
        auth_service.register_user(
            db,
            email="unit@example.com",
            password="12345678",
        )
        assert False
    except ValueError as e:
        assert str(e) == "User with this email already exists"


def test_authenticate_user_success(db):
    auth_service.register_user(
        db,
        email="unit@example.com",
        password="12345678",
    )

    user = auth_service.authenticate_user(
        db,
        email="unit@example.com",
        password="12345678",
    )

    assert user is not None
    assert user.email == "unit@example.com"


def test_authenticate_user_wrong_password(db):
    auth_service.register_user(
        db,
        email="unit@example.com",
        password="12345678",
    )

    user = auth_service.authenticate_user(
        db,
        email="unit@example.com",
        password="wrongpass",
    )

    assert user is None


def test_authenticate_user_not_found(db):
    user = auth_service.authenticate_user(
        db,
        email="missing@example.com",
        password="12345678",
    )

    assert user is None