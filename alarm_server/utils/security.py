"""Security utilities for password hashing and JWT token management."""
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config import config
from schemas.user import TokenData


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(user_id: int, username: str) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's database ID
        username: User's username

    Returns:
        JWT token as string
    """
    expire = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> TokenData | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")

        if user_id is None or username is None:
            return None

        return TokenData(user_id=user_id, username=username)
    except JWTError:
        return None
