from src.users.user_config import hash_protocol
def check_password_hash(pass1, pass2):
    if pass1 == hash_protocol(pass2).hexdigest():
        return True
    else:
        False
    

