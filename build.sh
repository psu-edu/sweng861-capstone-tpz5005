#!/bin/bash

echo "------------------------------------------"
echo "Preparing Environment..."
echo "------------------------------------------"

# Generate local SSL certificates
if [ ! -f "backend/cert.pem" ] || [ ! -f "backend/key.pem" ]; then
    echo "No SSL certificates found. Generating local certs for development..."
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out backend/cert.pem -keyout backend/key.pem \
        -days 365 -subj "/CN=localhost"
else
    echo "SSL certificates already exist. Skipping generation."
fi

echo "------------------------------------------"
echo "Generating custom login key..."
echo "------------------------------------------"

# Manage .env and CUSTOM_JWT_KEY
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No .env file found. Creating $ENV_FILE..."
    touch "$ENV_FILE"
fi

if ! grep -q "^CUSTOM_JWT_KEY=" "$ENV_FILE"; then
    echo "CUSTOM_JWT_KEY missing. Generating 256-bit key for HS256..."
    JWT_SECRET=$(openssl rand -hex 32)
    echo "CUSTOM_JWT_KEY=$JWT_SECRET" >> "$ENV_FILE"
    echo "CUSTOM_JWT_KEY added to $ENV_FILE."
else
    echo "CUSTOM_JWT_KEY already exists in $ENV_FILE. Skipping generation."
fi

echo "------------------------------------------"
echo "Building with Docker..."
echo "------------------------------------------"
docker-compose build --no-cache

echo "------------------------------------------"
echo "Building Complete!"
echo "-----"
echo "To start the application... "
echo "enter this command: docker-compose up"
echo "-----"
echo "To open the project, hold Control and"
echo "click the link 'https://localhost:3000/'"
echo "------------------------------------------"

## To build for development
## In the root directory
# python3 -m venv .venv
# source .venv/bin/activate
# pip install --upgrade pip
# pip install -r requirements.txt
# pip install fastapi uvicorn

## cd into /frontend 
# npm install
# npm run start-all