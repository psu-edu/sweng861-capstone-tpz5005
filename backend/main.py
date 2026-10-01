from fastapi import FastAPI, Request, Response, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os
from authlib.integrations.starlette_client import OAuth
from slowapi import Limiter
from slowapi.util import get_remote_address

#import pprint

from logger.logger import log_event
from security.github_auth import handle_user_login_data
from security.custom_auth import valid_user, create_jwt_token

from database.bookDatabase import init_book_db, populate_with_books

app = FastAPI(
    title="SWENG861 Capstone tpz5005",
    description="Capstone project for SWENG861",
    version="1.0"
)

# Configure CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

#----------- Authentication -----------#
# instantiate authentication object
oauth = OAuth()

# I will use github, as that is used commonly for SWENG861
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"})

app.add_middleware(SessionMiddleware, 
                   secret_key="secret_encryption_key",
                   same_site="lax",
                   https_only=True)
#--------------------------------------#

# A gateway for OSRS database specific endpoints
router = APIRouter(
    prefix="/api/bookstore/database",
    tags=["PSU Bookstore Gateway"]
)


# Service Provider login
# @info: This is the endpoint that re-directs the user to the external
#        github login page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/login")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("5/minute") # Only 5 logins per minute
async def login(request: Request):
    req_id = getattr(request.state, "request_id", None)

    # This redirect origin MUST match the frontend origin, otherwise 
    # the cookies will NOT SET for the frontend!!!!!
    redirect_uri = "https://localhost:8000/auth/callback" 

    log_event(
        level="INFO", 
        event_name="github_auth", 
        message="GitHub OAuth2 Login", 
        request_id=req_id
    )
    
    return await oauth.github.authorize_redirect(request, redirect_uri)


# Recieving end from the eternal github login page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/callback")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def auth_callback(request: Request):
    try:
        # Ask github to validate the login token and return an 
        # authentication token
        auth_token = await oauth.github.authorize_access_token(request)

        # With the auth token, ask github for information about user
        response_type = await oauth.github.get("user", token=auth_token)
        profile_info = response_type.json()

        # Saving this for debug purposes
        # print("---------- PROFILE INFO ----------")
        # pprint.pprint(profile_info)
        # print("----------------------------------")

        # If the email is private, we need to explicitly ask for an email
        # to recover any information
        if not profile_info.get("email"):
            email_resp = await oauth.github.get("user/emails", token=auth_token)
            emails = email_resp.json()
            for email in emails:
                if email.get("primary") and email.get("verified"):
                    profile_info["email"] = email.get("email")
                    break

        # store data in session cookie
        db_user = handle_user_login_data(profile_info)

        # store user data in session coockie
        request.session["user"] = db_user

        # Debug display info
        request.session["user"] = {
            "id": profile_info.get("id"),
            "username": profile_info.get("login"),
            "name": profile_info.get("name"),
            "avatar_url": profile_info.get("avatar_url"),
            "role": db_user["role"]
        }

        # if we are susseccful, redirect back to the frontend
        return RedirectResponse(url="https://localhost:3000/")

    # Throw debug error
    except Exception as error:
        raise HTTPException(status_code=400, detail="ERROR: Authentication failed")

    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.post("/auth/custom")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def login_custom(response: Response, user_data: dict):
    username = user_data.get("username")
    password = user_data.get("password")
    
    # Check the credentials
    if not valid_user(username, password):
        # Log failed login attempts
        
        log_event(
            level="WARNING",
            event_name="custom_login_failed",
            message=f"Failed custom login attempt for user '{username}'",
            username=username,
            auth_provider="custom"
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    # Generate a token
    token = create_jwt_token(username)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )

    # Log a successful login 
    log_event(
        level="INFO",
        event_name="auth_login_success",
        message=f"User '{username}' logged in successfully",
        username=username,
        auth_provider="custom"
    )
    
    return {
        "authenticated": True,
        "user": {"username": username},
        "access_token": token,
        "token_type": "bearer"
    }


# Logout user
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/logout")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def logout(request: Request):
    req_id = getattr(request.state, "request_id", None)
    user = request.session.get("user")
    username = user.get("username") if user else "unknown"

    request.session.clear()

    # Log the logout
    log_event(
        level="INFO",
        event_name="auth_logout",
        message=f"User '{username}' logged out",
        request_id=req_id,
        username=username
    )

    return RedirectResponse(url="https://localhost:3000/")


# Get active user data
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/user")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def get_active_user(request: Request):
    user = request.session.get("user")
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}

#####################################################################




@app.get("/api/hello")
def read_root():
    return {"message": "Hello from FastAPI backend!"}



#####################################################################

# Launch the backend server apon startup of the application
if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = 8000

    # for docker
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(base_dir, "cert.pem")
    key_path = os.path.join(base_dir, "key.pem")

    uvicorn.run("main:app", 
                host=HOST, 
                port=PORT, 
                reload=False,
                ssl_certfile=cert_path,
                ssl_keyfile=key_path)