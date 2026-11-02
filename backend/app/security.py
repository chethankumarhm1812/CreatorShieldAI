from datetime import datetime, timedelta, timezone
import bcrypt, jwt, hashlib
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models.models import User

bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(hashlib.sha256(password.encode()).digest(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    digest = hashed.encode()
    raw = password.encode()
    try:
        if bcrypt.checkpw(raw, digest):
            return True
    except ValueError:
        pass
    return bcrypt.checkpw(hashlib.sha256(raw).digest(), digest)

def create_token(user: User) -> str:
    payload = {"sub": str(user.id), "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except Exception as exc:
        raise HTTPException(401, "Invalid or expired token") from exc
    if not user:
        raise HTTPException(401, "User not found")
    return user

def require_roles(*roles):
    def checker(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker
