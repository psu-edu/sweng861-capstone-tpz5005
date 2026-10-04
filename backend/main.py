import traceback


from fastapi import Body, Depends, FastAPI, Request, Response, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os
from authlib.integrations.starlette_client import OAuth
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage

from pprint import pprint # DEBUG

from logger.logger import log_event

# Security Related Imports
from security.github_auth import handle_user_login_data, init_db
from security.custom_auth import valid_user, create_jwt_token
from security.security_utility import require_auth

# Database Related Imports
from database.book_database import init_book_db, populate_with_books, get_available_books, reserve_book
from database.equipment_database import init_equipment_db, populate_with_equipment, get_available_equipment, reserve_equipment

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

#--------------- Router ---------------#
# A gateway for OSRS database specific endpoints
router = APIRouter(
    prefix="/api/psu/bookstore",
    tags=["PSU Bookstore Gateway"]
)

# activate the router
app.include_router(router)
#--------------------------------------#

#----------- Database Init ------------#
# GitHub Auth
init_db() 

# Book Database
init_book_db()
populate_with_books()

# Equipment Database
init_equipment_db()
populate_with_equipment()
#--------------------------------------#


#####################################################################


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


# @info: Get Endpoint to query all the books in the library database
#-------------------------------------------------------------------#
@router.get("/books")
#-------------------------------------------------------------------#
def get_books(user: dict = Depends(require_auth)):

    available_books = get_available_books(datetime.now())

    return {"available_books": available_books}


# @info: Reserve endpoint that reserves a book in the book database
#-------------------------------------------------------------------#
@router.put("/reserve_book")
#-------------------------------------------------------------------#
def reserve_books(book_id: int = Body(...),
                  reservation_id: str = Body(...),
                  reserve_Start: datetime = Body(...),   
                  reserve_End: datetime = Body(...),
                  user: dict = Depends(require_auth)):

    created_by = user.get("username") or user.get("user")

    # Validate the input parameters
    if book_id is None or reservation_id is None or reserve_Start is None or reserve_End is None:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    # Reserve the book
    try:
        reservation_id = reserve_book(book_id, reservation_id, reserve_Start, reserve_End)
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err))

    log_event(
        level="INFO",
        event_name="Book Reservation",
        message=f"User '{created_by} reserved book with id: '{book_id}'",
        username=reservation_id,
        auth_provider=created_by
    )

    # We need to update the frontend, so get the updated available books after the reservation
    # Make sure you use the right time!!!
    updated_available_books = get_available_books(reserve_Start) 

    return {"status": "success", 
            "reservation_id": reservation_id,
            "updated_available_books": updated_available_books }

# @info: Get the availble equipment
#-------------------------------------------------------------------#
@router.get("/equipment")
#-------------------------------------------------------------------#
def get_equipment(user: dict = Depends(require_auth)):

    available_equipment = get_available_equipment(datetime.now())

    return {"available_equipment": available_equipment}


# @info: Reserve endpoint that reserves a book in the book database
#-------------------------------------------------------------------#
@router.put("/reserve_equipment")
#-------------------------------------------------------------------#
def reserve_equip(equipment_id: int = Body(...),
                  reservation_id: str = Body(...),
                  reserve_Start: datetime = Body(...),   
                  reserve_End: datetime = Body(...),
                  user: dict = Depends(require_auth)):

    created_by = user.get("username") or user.get("user")

    # Validate the input parameters
    if equipment_id is None or reservation_id is None or reserve_Start is None or reserve_End is None:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    # Reserve the equipment
    try:
        reservation_id = reserve_equipment(equipment_id, reservation_id, reserve_Start, reserve_End)
    except ValueError as err:
            raise HTTPException(status_code=409, detail=str(err)) 

    log_event(
        level="INFO",
        event_name="Equipment Reservation",
        message=f"User '{created_by} reserved book with id: '{equipment_id}'",
        username=reservation_id,
        auth_provider=created_by
    )

    # We need to update the frontend, so get the updated available equipment after the reservation
    # Make sure you use the right time!!!
    updated_available_equipment = get_available_equipment(reserve_Start) 

    return {"status": "success", 
            "reservation_id": reservation_id,
            "updated_available_equipment": updated_available_equipment }


# @info: Send an email receipt to the user when they have chacked out an item
#-------------------------------------------------------------------#
@router.put("/email_receipt")
#-------------------------------------------------------------------#
def email_notification(reservation_items: list = Body(...),
                       email_Addr: str = Body(...),
                       user: dict = Depends(require_auth)):

    created_by = user.get("username") or user.get("user")

    log_event(
        level="INFO",
        event_name="Email Receipt",
        message=f"User '{created_by} requested an email receipt at: '{email_Addr}'",
        username=created_by,
        auth_provider=created_by
    )

   # Assemble the body
    body_text = "Here is your reservation receipt from the PSU Bookstore:\n\n"
    
    for item in reservation_items:
        body_text += f"Item: {item.get('item_type')} - {item.get('item')}\n"
        body_text += f"Reservation ID: {item.get('reservation_id')}\n"
        body_text += f"Start: {item.get('reserve_start')}\n"
        body_text += f"End: {item.get('reserve_end')}\n"
        body_text += "-" * 30 + "\n"
        
    body_text += "\nThank you for your reservation!"

    # construct the email
    msg = EmailMessage()
    msg.set_content(body_text)
    msg['Subject'] = "Your Reservation Receipt"
    msg['From'] = ""  # This is a sender email
    msg['To'] = email_Addr  # Target email

    # Send the email
    try:
        # Example using Gmail's SMTP server
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "" # This is the sender email
        sender_password = "" # This is the google App Code

        # Connect, login, and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() 
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        
        return {"status": "success"}

    except Exception as e:
        print(f"Failed to send email: {e}")
        # Return a 500 status or similar if you want the frontend to know it failed
        return {"status": "error", "message": str(e)}


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