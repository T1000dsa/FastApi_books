from datetime import datetime, timedelta

import bcrypt
import jwt
from src.users.user_models import UserModel as db_user
from src.core.config import authJWT

TOKEN_TYPE = "type"
ACCESS_TYPE = 'access_token'
REFRESH_TYPE = 'refresh_token'

# >>> private_key = b"-----BEGIN PRIVATE KEY-----\nMIGEAgEAMBAGByqGSM49AgEGBS..."
# >>> public_key = b"-----BEGIN PUBLIC KEY-----\nMHYwEAYHKoZIzj0CAQYFK4EEAC..."



def encode_jwt(
    payload: dict,
    private_key: str = authJWT.private_key_path.read_text(),
    algorithm: str = authJWT.algorithm,
    expire_minutes: int = authJWT.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    to_encode = payload.copy()
    now = datetime.utcnow()
    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expire_minutes)
    to_encode.update(
        exp=expire,
        iat=now,
    )
    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorithm,
    )
    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = authJWT.public_key_path.read_text(),
    algorithm: str = authJWT.algorithm,
) -> dict:
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
    )
    return decoded

async def create_jwt(
        token_type:str, 
        payload:dict,
        expire_minutes: int = authJWT.access_token_expire_minutes,
        expire_timedelta: timedelta | None = None
        ):
    
    token_payload = {TOKEN_TYPE:token_type}
    payload.update(token_payload)
    
    return encode_jwt(
        payload=payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta
        )


async def create_refresh_token(user:db_user):
    jwt_payload = {
        'username':user.username,
    }
    return await create_jwt(
        token_type=REFRESH_TYPE, 
        payload=jwt_payload,
        expire_minutes=authJWT.refresh_token_expire_minutes,
        )

async def create_access_token(user:db_user):
    jwt_payload = {
        'username':user.username,
    }
    return await create_jwt(
        token_type=ACCESS_TYPE, 
        payload=jwt_payload,
        expire_minutes=authJWT.access_token_expire_minutes,
        )