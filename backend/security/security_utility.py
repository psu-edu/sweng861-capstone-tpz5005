import jwt
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .custom_auth import ALGORITHM, SECRET_KEY

# Security object for custom authentication
security = HTTPBearer(auto_error=False)

# Authentication verification helper function
#-------------------------------------------------------------------#
async def require_auth(request: Request,
                       auth: HTTPAuthorizationCredentials = Depends(security) ) -> dict:
#-------------------------------------------------------------------#
    # First check for a custom authentication token
    if auth and auth.credentials:
        try:
            payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                return {"user": username, "auth_type": "custom_jwt"}
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid JWT token")
    
    # If no custom token, check for GitHub
    user = request.session.get("user")

    # if its null/failure throw an error
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication access token is required")

    return user



#-------------------------------------------------------------------#
async def require_admin(current_user: dict = Depends(require_auth)) ->dict:
#-------------------------------------------------------------------#
    # If the user is not an admin
    if current_user.get("role") != "admin":
        # throw an error
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN,
                                    detail="Admin privlages required")
    
    return current_user

#-------------------------------------------------------------------#
def verify_owner_or_admin(current_user: dict, owner_id: int):
#-------------------------------------------------------------------#
    is_owner = current_user["id"] == owner_id
    is_admin = current_user.get("role") == "admin"

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to use this endpoint"
        )
        
    return current_user