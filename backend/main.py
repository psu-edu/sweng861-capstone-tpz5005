from fastapi import FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import jwt
import uvicorn
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Security object for custom authentication
security = HTTPBearer(auto_error=False)

app = FastAPI()

# Configure CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hello")
def read_root():
    return {"message": "Hello from FastAPI backend!"}

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