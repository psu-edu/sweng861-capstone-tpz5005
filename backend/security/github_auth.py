import sqlite3
from datetime import datetime, timezone

DB_name = "authentic_users.db"

#-----------------------------------------------#
def init_db():
#-----------------------------------------------#
    """ Create table if it does not exist"""
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id TEXT UNIQUE NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Central handle function
# @description: Takes in information from a successful login,
#               and checks to see if the user exists in the database.
#               If the user does exist, the last login time is updated.
#-----------------------------------------------#
def handle_user_login_data(user_profile_data: dict) -> dict:
#-----------------------------------------------#
    provider_id = str(user_profile_data.get("id"))
    email = user_profile_data.get("email")

    # get the database
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()

    # Check to see if the profile_id exists in the databbase
    query = "SELECT * FROM users WHERE provider_id = ?"
    cursor.execute(query, (provider_id,))
    row = cursor.fetchone()
    conn.close()

    #if not found, create a new user
    if row is None:
        return create_user(provider_id, email)   
    # else update time
    else:
        return update_user_login(provider_id, email)

# Creates a new user in the database
#-----------------------------------------------#
def create_user(provider_id: str, 
                email: str | None, 
                role: str = "user") -> dict:
#-----------------------------------------------#
    # get the current time
    now = datetime.now(timezone.utc).isoformat()

    # connect to the database
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()

    # insert the new user information
    cursor.execute("""
        INSERT INTO users (provider_id, email, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (provider_id, email, role, now, now))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": user_id,
            "provider_id": provider_id, 
            "email": email,
            "role": role,
            "creted_at": now,
            "updated_at": now}

# Update timestamp information for an already-existing user
#-----------------------------------------------#
def update_user_login(provider_id: str, email: str | None) -> dict:
#-----------------------------------------------#
    # get the current time
    now = datetime.now(timezone.utc).isoformat()

    # connect to the database
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()

    # update the user's login information
    cursor.execute("""
        UPDATE users
        SET email = ?, updated_at = ?
        WHERE provider_id = ?
    """, (email, now, provider_id))
    conn.commit()

    # need to get the data to return it
    cursor.execute("""
        SELECT * FROM users WHERE provider_id = ?
    """, (provider_id,))
    row = cursor.fetchone()

    conn.close()

    # this isnt the best implementation, but it works for now
    return {
        "id": row[0],
        "provider_id": row[1],
        "email": row[2],
        "role": row[3],
        "created_at": row[4],
        "updated_at": row[5]
    }

# Get function that retruns the value of a field
# @param - user_id: The id of the user
# @param - field_name: the name of the field you're searching for 
#-----------------------------------------------#
def get_data_field(user_id: int, field_name: str) -> str | int | None:
#-----------------------------------------------#
    # Validate desired field
    valid_fields = {"id", "provider_id", "email", "created_at", "updated_at"}
    if field_name not in valid_fields:
        raise ValueError(f"Invalid field {field_name} being queried")

    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()

    query = f"SELECT {field_name} FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    return row[0]

# Utility debug function for viewing database info
#-----------------------------------------------#
def print_database_info() -> dict:
#-----------------------------------------------#
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()

    # get all information
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    conn.close()

    # print all
    return {"users": rows}