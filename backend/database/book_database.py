import sqlite3
from dotenv import load_dotenv
from datetime import datetime, timezone

from .data.book_list import books

load_dotenv()

db_name = "book_db"

# gets the connection object to the database
#-----------------------------------------------#
def get_connection():
#-----------------------------------------------#
    connection = sqlite3.connect(db_name)
    connection.row_factory = sqlite3.Row
    return connection


# Initialize the database
#-----------------------------------------------#
def init_book_db():
#-----------------------------------------------#
    with get_connection() as connection:

        # Enable foreign key enforcement
        connection.execute("PRAGMA foreign_keys = ON")
        
        # Table for abstracted book information
        connection.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                copies INTEGER NOT NULL DEFAULT 1
                    CHECK (copies >= 0)
            )
        """)

        # Table for information relating to RESERVATIONS
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                reserved_by TEXT NOT NULL,
                reserve_start TEXT NOT NULL,
                reserve_end TEXT NOT NULL,

                FOREIGN KEY (book_id)
                    REFERENCES books(id)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()


#Info: Function to add books to database (Create)
# Params
#   book_id - The ID of the book
#   title - The title of the book
#   genre - The genre of the book
#   copies - How many copies are being entered
#---------------------------------------------------------#
def add_book(book_id, title, genre, copies):
#---------------------------------------------------------#
    # get a connection to db
    with get_connection() as connection:
        # Add the book
        connection.execute("""
            INSERT INTO books (id, title, genre, copies)
            VALUES(?, ?, ?, ?)
        """, (book_id, title, genre, copies)
        )

        connection.commit()


# Info: Get the available book by time (Read)
# Params
#   requested_time - The time in which available books will
#                    be queried
#---------------------------------------------------------#
def get_available_books(requested_time: datetime):
#---------------------------------------------------------#
    # print("\n========== AVAILABILITY CHECK ==========")
    # print("Requested time:", requested_time)
    time_str = requested_time.isoformat()

    with get_connection() as connection:

        books = connection.execute("""
            SELECT
                b.id,
                b.title,
                b.genre,
                b.copies,
                COUNT(r.id) AS reservation_count,
                b.copies - COUNT(r.id) AS available_copies
            FROM books b
            LEFT JOIN reservations r
                ON b.id = r.book_id
                AND r.reserve_start <= ?
                AND r.reserve_end > ?
            GROUP BY
                b.id,
                b.title,
                b.genre,
                b.copies
            ORDER BY b.id
        """, (time_str, time_str)).fetchall()

        return [dict(book) for book in books]


# Info: Gets available books by genre
# Params
#   genre - The genre to be queried
#   requested_time - the time to be queried
#---------------------------------------------------------#
def get_books_by_genre(genre, requested_time):
#---------------------------------------------------------#
    time_str = requested_time.isoformat()

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                b.id,
                b.title,
                b.genre,
                b.copies,
                b.copies - COUNT(r.id) AS available_copies
            FROM books b
            LEFT JOIN reservations r
                ON b.id = r.book_id
                AND r.reserve_start <= ?
                AND r.reserve_end >= ?
            WHERE LOWER(b.genre) = LOWER(?)
            GROUP BY
                b.id,
                b.title,
                b.genre,
                b.copies
            HAVING b.copies - COUNT(r.id) > 0
        """, (time_str, time_str, genre)).fetchall()

    return [dict(row) for row in rows]


# Info: Reserve a book in the databse (Update/Delete)
# Params
#   book_id - The ID of the book
#   student_email - The email fo the student for item 
#                   ownership purposes
#   reserve_start - The start time of the reserve window
#   reserve_end - The end time of the reserve window
#---------------------------------------------------------#
def reserve_book(book_id, student_email, reserve_start, reserve_end):
#---------------------------------------------------------#

    # Validate timezone info
    if reserve_start.tzinfo is None or reserve_end.tzinfo is None:
        raise ValueError("Reservation times must include a timezone")

    # Convert both times to UTC 
    reserve_start = reserve_start.astimezone(timezone.utc)
    reserve_end = reserve_end.astimezone(timezone.utc)

    # Validate reservationw indow
    if reserve_end <= reserve_start:
        raise ValueError("Reservation end must be after start")

    # Get a connection
    with get_connection() as connection:

        # Begin immediate will prevent another user from reserving the same copy
        connection.execute("BEGIN IMMEDIATE")

        # Get the number of copies available
        book = connection.execute("""
            SELECT copies
            FROM books
            WHERE id = ?
        """, (book_id,)).fetchone()

        # If the book ID doesn't exist, reject the request.
        if book is None:
            raise ValueError("Book not found")

        # Get the number of available copies
        total_copies = book["copies"]

        # Find all reservations for this book that overlap
        # the requested reservation window.
        #
        # The intervals are half-open:
        #   Existing start < requested end
        #   Existing end   > requested start
        #
        # This allows one reservation to end exactly when
        # another reservation begins.
        reservations = connection.execute("""
            SELECT reserve_start, reserve_end
            FROM reservations
            WHERE book_id = ?
              AND reserve_start < ?
              AND reserve_end > ?
        """, (
            book_id,
            reserve_end.isoformat(),
            reserve_start.isoformat()
        )).fetchall()

        # Create a dictionary to record when existing
        # reservations start and end.
        events = {}

        # For each reservation that overlaps
        for reservation in reservations:

            # Convert to datetime
            existing_start = datetime.fromisoformat(
                reservation["reserve_start"]
            ).astimezone(timezone.utc)

            existing_end = datetime.fromisoformat(
                reservation["reserve_end"]
            ).astimezone(timezone.utc)

            # Restrict the existing reservation to the portion
            # that overlaps the new requested time window.
            overlap_start = max(reserve_start, existing_start)
            overlap_end = min(reserve_end, existing_end)

            # Record the start of the overlap as one more
            # occupied copy.
            events[overlap_start] = events.get(overlap_start, 0) + 1

            # Record the end of the overlap as one freed copy.
            events[overlap_end] = events.get(overlap_end, 0) - 1

        # Track how many copies are currently reserved as we
        # move through the reservation events chronologically.
        active_copies = 0

        # Max number of reserved copies
        max_reserved = 0

        # Sort the events by timestamp so that reservations
        # are processed in chronological order.
        for event_time in sorted(events):

            # Add or subtract the number of copies associated
            # with this event (start = +1, end = -1).
            active_copies += events[event_time]

            # Update the maximum concurrent reservations seen.
            max_reserved = max(max_reserved, active_copies)

        # If the maximum number of existing reservations is
        # equal to or greater than the total inventory, then
        # there isn't a copy available for the entire window.
        if max_reserved >= total_copies:
            raise ValueError(
                "No copies available for the requested time"
            )

        # At least one copy is available throughout the
        # requested interval, so insert the new reservation.
        cursor = connection.execute("""
            INSERT INTO reservations (
                book_id,
                reserved_by,
                reserve_start,
                reserve_end
            )
            VALUES (?, ?, ?, ?)
        """, (
            book_id,
            student_email,
            reserve_start.isoformat(),
            reserve_end.isoformat()
        ))

        # Return the ID assigned to this newly created
        # reservation so the endpoint can send it to
        # the frontend.
        return cursor.lastrowid

# Get function for reading all reserved books
#-----------------------------------------------#
def get_all_reservations():
#-----------------------------------------------#
    with get_connection() as connection:

        connection.execute("PRAGMA foreign_keys = ON")

        reservations = connection.execute("""
            SELECT
                id,
                book_id,
                reserved_by,
                reserve_start,
                reserve_end
            FROM reservations
        """).fetchall()

        return [dict(reservation) for reservation in reservations]


# Helper function to populate the database
#---------------------------------------------------------#
def populate_with_books():
#---------------------------------------------------------#
    with get_connection() as connection:
        # Note: If you want the data to persist between runs, remove the
        # following lines that delete the existing data.
        # Remove existing reservations first
        connection.execute("DELETE FROM reservations")

        # Remove existing books
        connection.execute("DELETE FROM books")

        # Insert data from the book list
        connection.executemany("""
        INSERT OR IGNORE INTO books (id, title, genre, copies)
        VALUES(?, ?, ?, ?)
        """, books)

        connection.commit()

# Helper function to create dummy reservations
#-----------------------------------------------#
def populate_with_reservations():
#-----------------------------------------------#
    with get_connection() as connection:

        reservations = [
            (1, "student@psu.edu", 
             "2026-10-01T09:00:00+00:00",
             "2026-10-05T17:00:00+00:00"),

            (2, "professor@psu.edu",
             "2026-10-10T10:00:00+00:00",
             "2026-10-15T16:00:00+00:00"),

            (3, "student2@psu.edu",
             "2026-11-01T08:00:00+00:00",
             "2026-11-07T18:00:00+00:00"),

            (1, "professor@psu.edu",
             "2026-12-01T09:00:00+00:00",
             "2026-12-10T17:00:00+00:00")
        ]

        connection.executemany("""
            INSERT INTO reservations (
                book_id,
                reserved_by,
                reserve_start,
                reserve_end
            )
            VALUES (?, ?, ?, ?)
        """, reservations)

        connection.commit()

#---------------------------------------------------------#
def debug_book_state(connection, label):
#---------------------------------------------------------#
    print(f"\n===== {label} =====")

    books = connection.execute("""
        SELECT id, title, copies
        FROM books
        ORDER BY id
    """).fetchall()

    for book in books:
        print(
            f"BOOK id={book['id']} "
            f"title={book['title']} "
            f"copies={book['copies']}"
        )

    reservations = connection.execute("""
        SELECT id, book_id, reserved_by, reserve_start, reserve_end
        FROM reservations
        ORDER BY id
    """).fetchall()

    print("RESERVATIONS:")

    for reservation in reservations:
        print(dict(reservation))

    print("====================\n")