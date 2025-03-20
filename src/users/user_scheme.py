from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ValidationInfo


class PasswordTrouble(Exception):
    def __init__(self, message, *args):
        self.message = message # without this you may get DeprecationWarning
        # Special attribute you desire with your Error, 
        # perhaps the value that caused the error?:       
        # allow users initialize misc. arguments as any other builtin Error
        super(PasswordTrouble, self).__init__(message, *args) 

class User(BaseModel):
    username:str
    password:str
    password_again:str
    mail:str|None
    bio:str|None


    @field_validator("username")
    @classmethod
    def check_valid_length_username(cls, username: str) -> str:
        if len(username) > 128:
                raise ValueError("Too long username", 'User')
        return username
    
    @field_validator("password")
    @classmethod
    def check_valid_length_password(cls, password: str) -> str:
        if len(password) > 256:
            raise ValueError("Too long password", 'Pass')
        if len(password) < 10:
            raise ValueError("Too short password", 'Pass')

        return password


    @field_validator("mail")
    @classmethod
    def check_valid_length_mail(cls, mail: str) -> str:
        if mail:
            if len(mail) > 128:
                raise ValueError("Too long mail", 'Mail')
            return mail
        return None
    

    @field_validator("bio")
    @classmethod
    def check_valid_length_bio(cls, bio: str) -> str:
        if len(bio) > 256:
            raise ValueError("Too long Bio", 'Bio')
        return bio
    

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_again:
            raise ValueError("Passwords do not match", 'Pass')
        return self

