from src.users.user_config import hash_protocol
import ast
def check_password_hash(pass1, pass2):
    try:
        pass2_bytes = ast.literal_eval(pass2)  # Safely evaluate the string into bytes
    except (ValueError, SyntaxError):
        # Handle invalid stored hash format
        return False
    return hash_protocol.checkpw(pass1.encode(), pass2_bytes)
