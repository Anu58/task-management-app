from sqlalchemy.orm import Session
from fastapi import HTTPException, status , Request
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
from src.utils.settings import settings
from src.users.dtos import UserSchema, LoginSchema
from src.users.models import UserModel


# Password hashing setup
password_hash = PasswordHash.recommended()



def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def register(body: UserSchema, db: Session):
    # Check username exists
    is_user = db.query(UserModel).filter(UserModel.username == body.username).first()
    if is_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check email exists
    is_email = db.query(UserModel).filter(UserModel.email == body.email).first()
    if is_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Hash password
    hashed_password = get_password_hash(body.password)

    # Create new user
    new_user = UserModel(
        name=body.name,
        username=body.username,
        email=body.email,
        hash_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "name": new_user.name,
        "username": new_user.username,
        "email": new_user.email,
        "hash_password": new_user.hash_password
    }


def login_user(body: LoginSchema, db: Session):
    user = db.query(UserModel).filter(UserModel.username == body.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You entered wrong username"
        )

    if not verify_password(body.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You entered wrong password"
        )

    # Generate JWT Token
    exp_time = datetime.now() + timedelta(minutes=settings.EXP_TIME)
    print(exp_time)
    token = jwt.encode(
        {"_id": user.id,"exp": exp_time.timestamp()},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return {"token": token}

## Token send 

def is_authenticated(request: Request, db: Session):
    try:

        token = request.headers.get("Authorization")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are unauthorized"
            )

        token = token.split(" ")[-1]

        data = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = data.get("_id")

        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are unauthorized"
            )

        return user

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are unauthorized"
        )