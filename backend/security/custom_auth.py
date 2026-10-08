import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
import os


# JWT Settings (Keep your secret key in your .env file in a real app!)
# SECRET_KEY = os.getenv("CUSTOM_JWT_KEY") # original
SECRET_KEY = os.getenv("CUSTOM_JWT_KEY", "dev_default_secret_key_123") # ADDED FOR UNIT TESTING
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Utility Function
#-------------------------------------------------------------------#
def hash_password(password: str) -> str:
#-------------------------------------------------------------------#
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


custom_users = {
    "abc1234@psu.edu": {
        "username": "student",
        "hashed_password": hash_password("PennState1855"),
        "role": "student" 
    },
    "prof456@psu.edu": {
        "username": "professor",
        "hashed_password": hash_password("professor123"),
        "role": "admin" 
    }
}


#-------------------------------------------------------------------#
def verify_password(plain_password: str, hashed_password: str) -> bool:
#-------------------------------------------------------------------#
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


#-------------------------------------------------------------------#
def valid_user(username: str, plain_password: str) -> bool:
#-------------------------------------------------------------------#
    """Checks if the user exists and the password matches the hash."""
    user = custom_users.get(username)
    if not user:
        return False
    # Passlib does the magic of comparing the raw password to the hash
    return verify_password(plain_password, user["hashed_password"])


#-------------------------------------------------------------------#
def create_jwt_token(username: str) -> str:
#-------------------------------------------------------------------#
    # Token is valid for 60 minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # The 'payload' is the data packed inside the token
    payload = {
        "sub": username,
        "exp": expire 
    }
    
    # Encode it using your secret key
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Gets the role of the authenticated user
#-------------------------------------------------------------------#
def get_user_role(username: str) -> str | None:
#-------------------------------------------------------------------#
    user = custom_users.get(username)

    if user:
        return user["role"]

    return None