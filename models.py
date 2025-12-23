import hashlib
import duckdb
from fastapi.responses import RedirectResponse
import jwt

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from log import logger

SECRET_KEY = "efe2619e45edfdc1b1e14d5e0a6b68b98e010bcc77ff6188370ecd1f11664e37"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class CustomBaseModel(BaseModel):
    @classmethod
    def from_list(cls, tpl):
        return cls(**{k: v for k, v in zip(cls.model_fields.keys(), tpl)})

class User(CustomBaseModel):
    id: Optional[int] = None
    username: str
    prof_img_url: Optional[str] = None
    is_admin: bool = False
    points: int = 0
    number_games_won: int = 0
    is_activated: bool = False
    created_at: Optional[datetime] = None

class AuthUser(CustomBaseModel):
    username: str
    hashpsw: str

class Token(CustomBaseModel):
    access_token: str
    token_type: str
class TokenData(CustomBaseModel):
    username: str | None = None

def hash_this_password(password: str):
    salt = "iamateapotshortandstout"
    # hash this
    myHash = hashlib.sha256(password.encode('utf-8'))
    hexDigest = myHash.hexdigest()
    # add the salt
    finalHash = hexDigest + salt
    return finalHash

def get_auth_user(username: str):
    '''
    Returns the user or None
    '''
    with duckdb.connect("app.db") as con:
        return con.sql(f"SELECT * FROM auth WHERE username = '{username}'").fetchone()

def verify_password(password: str, hashed_password: str):
    testingPsw = hash_this_password(password)
    return hashed_password == testingPsw

def auth_this_user(username: str, password: str):
    authUser = get_auth_user(username)
    if not authUser:
        return False
    if not verify_password(password, authUser[1]):
        return False
    return AuthUser(username=username, hashpsw=authUser[1])

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")

    if token is None:
        raise HTTPException(status_code=303, headers={"Location": "/landing"})

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            logger.error("No username found, redirecting to landing")
            raise HTTPException(status_code=303, headers={"Location": "/landing"})
        
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        # raise credentials_exception
        logger.error("Invalid token, redirecting to landing")
        raise HTTPException(status_code=303, headers={"Location": "/landing"})
    
    user = None
    with duckdb.connect("app.db") as con:
        res = con.sql(f"SELECT * FROM users WHERE username = '{token_data.username}'").fetchone()
        if res is not None:
            user = User.from_list(res)

    if user is None:
        # raise credentials_exception
        logger.error("User is not logged in")
        raise HTTPException(status_code=303, headers={"Location": "/landing"})

    return user

async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={'Location': "/"})

    return current_user

# ----- other relevant bingo models -----

class Bingo(CustomBaseModel):
    id: Optional[int] = None
    completed: bool = False
    victor: Optional[int] = None  # FK -> users.id
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class UserBingoProgress(CustomBaseModel):
    user_id: int        # FK -> users.id
    bingo_id: int       # FK -> bingo.id
    completed_index: int


class UserWin(CustomBaseModel):
    user_id: int        # FK -> users.id
    bingo_id: int       # FK -> bingo.id


class UserGameClicks(CustomBaseModel):
    user_id: int        # FK -> users.id
    bingo_id: int       # FK -> bingo.id
    clicks: int = 1


class Prompt(CustomBaseModel):
    bingo_game: int     # FK -> bingo.id
    idx: int            # [0, 16] position on the board
    prompt: str
    created_at: Optional[datetime] = None
