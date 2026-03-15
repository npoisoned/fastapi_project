from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


class AuthService:
    def register_user(self, db: Session, email: str, password: str) -> User:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User with this email already exists")

        user = User(
            email=email,
            password_hash=hash_password(password),
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate_user(self, db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user


auth_service = AuthService()