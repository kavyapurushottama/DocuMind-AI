from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import SignupRequest


def create_user(db: Session, data: SignupRequest) -> User:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise ValueError("An account with this email already exists")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def reset_password(db: Session, email: str, new_password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("No account found with this email address")
    if len(new_password) < 6:
        raise ValueError("Password must be at least 6 characters")
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def issue_token(user: User) -> str:
    return create_access_token(subject=str(user.id))
