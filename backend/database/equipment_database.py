import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

db_name = "equipment_db"

# gets the connection object to the database
#-----------------------------------------------#
def get_connection():
#-----------------------------------------------#
    connection = sqlite3.connect(db_name)
    connection.row_factory = sqlite3.Row
    return connection

# initialize the database
#-----------------------------------------------#
def init_equipment_db():
#-----------------------------------------------#
    with get_connection() as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                copies INTEGER NOT NULL DEFAULT 1
                    CHECK (copies >= 0)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS equipment_reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                reserved_by TEXT NOT NULL,
                reserve_start TEXT NOT NULL,
                reserve_end TEXT NOT NULL,

                FOREIGN KEY (equipment_id)
                    REFERENCES equipment(id)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()


#-----------------------------------------------#
def reserve_equipment(equipment_id, 
                      student_email, 
                      reserve_start, 
                      reserve_end):
#-----------------------------------------------#
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO equipment_reservations (
                equipment_id,
                reserved_by,
                reserve_start,
                reserve_end
            )
            VALUES (?, ?, ?, ?)
        """, (
            equipment_id,
            student_email,
            reserve_start.isoformat(),
            reserve_end.isoformat()
        ))

        connection.commit()


#-----------------------------------------------#
def get_equipment_by_time(requested_time: datetime):
#-----------------------------------------------#
    time_str = requested_time.isoformat()

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                e.id,
                e.name,
                e.equipment_type,
                e.manufacturer,
                e.model,
                e.copies,
                e.copies - COUNT(r.id) AS available_copies
            FROM equipment e
            LEFT JOIN equipment_reservations r
                ON e.id = r.equipment_id
                AND r.reserve_start <= ?
                AND r.reserve_end >= ?
            GROUP BY
                e.id,
                e.name,
                e.equipment_type,
                e.manufacturer,
                e.model,
                e.copies
            HAVING available_copies > 0
        """, (time_str, time_str)).fetchall()

    return [dict(row) for row in rows]


#-----------------------------------------------#
def get_equipment_by_type(equipment_type):
#-----------------------------------------------#
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM equipment
            WHERE equipment_type = ?
        """, (equipment_type,)).fetchall()

    return [dict(row) for row in rows]