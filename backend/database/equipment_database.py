import sqlite3
from dotenv import load_dotenv
from datetime import datetime, timezone

from .data.equipment_list import equipment

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
                type TEXT NOT NULL,
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
def reserve_equipment( equipment_id,
                       student_email,
                       reserve_start,
                       reserve_end ):
#-----------------------------------------------#
    # Make sure the datetimes contain timezone info
    if reserve_start.tzinfo is None or reserve_end.tzinfo is None:
        raise ValueError(
            "Reservation times must include a timezone"
        )

    # Normalize to UTC.
    reserve_start = reserve_start.astimezone(timezone.utc)
    reserve_end = reserve_end.astimezone(timezone.utc)

    # Make sure the reservation has a valid duration
    if reserve_end <= reserve_start:
        raise ValueError(
            "Reservation end must be after start"
        )

    with get_connection() as connection:

        # Prevent another reservation from being inserted
        # simultaneously
        connection.execute("BEGIN IMMEDIATE")

        # Get the total number of copies.
        equipment = connection.execute("""
            SELECT copies
            FROM equipment
            WHERE id = ?
        """, (equipment_id,)).fetchone()

        if equipment is None:
            raise ValueError("Equipment not found")

        total_copies = equipment["copies"]

        # Find reservations for THIS equipment that overlap
        # the requested reservation.
        reservations = connection.execute("""
            SELECT
                reserve_start,
                reserve_end
            FROM equipment_reservations
            WHERE equipment_id = ?
              AND reserve_start < ?
              AND reserve_end > ?
        """, (
            equipment_id,
            reserve_end.isoformat(),
            reserve_start.isoformat()
        )).fetchall()

        # Track when existing equipment becomes occupied
        # and when it becomes available again
        events = {}

        for reservation in reservations:

            existing_start = datetime.fromisoformat(
                reservation["reserve_start"]
            ).astimezone(timezone.utc)

            existing_end = datetime.fromisoformat(
                reservation["reserve_end"]
            ).astimezone(timezone.utc)

            # Only consider the portion of the existing
            # reservation that overlaps our requested period
            overlap_start = max(
                reserve_start,
                existing_start
            )

            overlap_end = min(
                reserve_end,
                existing_end
            )

            # +1 means one copy becomes occupied.
            events[overlap_start] = (
                events.get(overlap_start, 0) + 1
            )

            # -1 means one copy becomes available.
            events[overlap_end] = (
                events.get(overlap_end, 0) - 1
            )

        # Calculate the maximum number of copies that are
        # simultaneously reserved during this period
        active_copies = 0
        max_reserved = 0

        for event_time in sorted(events):
            active_copies += events[event_time]

            max_reserved = max(
                max_reserved,
                active_copies
            )

        # If all copies are already reserved at any point
        # during the requested period, this new reservation
        # cannot be created.
        if max_reserved >= total_copies:
            raise ValueError(
                "No copies available for the requested time"
            )

        # There is at least one copy available, so create
        # the reservation.
        cursor = connection.execute("""
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

        return cursor.lastrowid


#-----------------------------------------------#
def get_available_equipment(requested_time: datetime):
#-----------------------------------------------#
    time_str = requested_time.isoformat()

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                e.id,
                e.name,
                e.type,
                e.manufacturer,
                e.model,
                e.copies,
                e.copies - COUNT(r.id) AS available_copies
            FROM equipment e
            LEFT JOIN equipment_reservations r
                ON e.id = r.equipment_id
                AND r.reserve_start <= ?
                AND r.reserve_end > ?
            GROUP BY
                e.id,
                e.name,
                e.type,
                e.manufacturer,
                e.model,
                e.copies
            ORDER BY e.id
        """, (time_str, time_str)).fetchall()

    return [dict(row) for row in rows]


#-----------------------------------------------#
def get_equipment_by_type(equipment_type):
#-----------------------------------------------#
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM equipment
            WHERE type = ?
        """, (equipment_type,)).fetchall()

    return [dict(row) for row in rows]


# Helper function to populate the database
#---------------------------------------------------------#
def populate_with_equipment():
#---------------------------------------------------------#
    with get_connection() as connection:
        # Note: If you want the data to persist between runs, remove the
        # following lines that delete the existing data.
        # Remove existing reservations first
        connection.execute("DELETE FROM equipment_reservations")

        # Remove existing equipment
        connection.execute("DELETE FROM equipment")

        connection.executemany("""
        INSERT OR IGNORE INTO equipment (id, name, type, manufacturer, model, copies)
        VALUES(?, ?, ?, ?, ?, ?)
        """, equipment)

        connection.commit()