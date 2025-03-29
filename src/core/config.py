import os
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
import logging

max_file_size = 10 * 1024 * 1024
base_dir = Path(__file__).parent.parent
media_root = base_dir / "media_root" / datetime.now().date().strftime('%Y/%m/%d')

TOKEN_TYPE = "type"
ACCESS_TYPE = 'access_token'
REFRESH_TYPE = 'refresh_token'

access_token_expire:int = 15
refresh_token_expire:int =60*60*24*30

if os.path.exists(media_root) == False:
    os.makedirs(media_root, exist_ok=True)

class AuthJWT(BaseModel):
    private_key_path:Path = base_dir / 'certf' / 'jwt-private.pem'
    public_key_path:Path = base_dir / 'certf' / 'jwt-public.pem'
    algorithm:str = 'RS256'
    access_token_expire_minutes:int = access_token_expire
    refresh_token_expire_minutes:int = refresh_token_expire

authJWT = AuthJWT()


logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')
