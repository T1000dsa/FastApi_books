from src.database_data.database import Base, int_pk, created_at, updated_at
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.users.user_config import hash_protocol
from src.users.services import check_password_hash

class User(Base):
    __tablename__ = 'users'

    id:Mapped[int_pk]
    username:Mapped[str]
    password:Mapped[str]
    mail:Mapped[str|None]
    bio:Mapped[str|None]
    join_data:Mapped[created_at]
    last_time_login:Mapped[updated_at]

    is_super_user:Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_super_user={self.is_super_user})>"
    
    def set_password(self, password:str):
        self.password = hash_protocol(password.encode()).hexdigest()

    def check_password(self, check_pass):
        return check_password_hash(self.password, check_pass)