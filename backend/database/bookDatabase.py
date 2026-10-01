import sqlite3
from dotenv import load_dotenv
from datetime import datetime

from book_list import books

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
    time_str = requested_time.isoformat()

    with get_connection as connection:
        rows = connection.execute("""
            SELECT 
                b.id,
                b.title,
                b.genre,
                b.copies,
                COUNT(r.id) AS available_copies
            FROM books b
            LEFT JOIN reservations r
                ON b.id = r.book_id
                AND r.reserve_start <= ?
                AND r.reserve_end >= ?
            GROUP BY
                b.id,
                b.title,
                b.genre,
                b.copies
            HAVING available_copies > 0
        """, (time_str, time_str)).fetchall()

    return [dict(row) for row in rows]


# Info: Reserve a book in the databse (Update/Delete)
# Params
#   book_id - The ID of the book
#   student_email - The email fo the student for item 
#                   ownership purposes
#   reserve_start - The start time of the reserve window
#   reserve_end - The end time of the reserve window
#---------------------------------------------------------#
def reserve_book( book_id, 
                  student_email, 
                  reserve_start, 
                  reserve_end):
#---------------------------------------------------------#
    # get a connection to db
    with get_connection() as connection:
        # we are accessing the RESERVE TABLE -- remember that!
        connection.execute("""
            INSERT INTO reservations (
                book_id,
                reverved_by
                reserve_start
                reserve_end
            )
            VALUES (?, ?, ?, ?)
        """, ( book_id,
               student_email,
               reserve_start.isoformat(),
               reserve_end.isoformat(),
        ))

        connection.commit()


def populate_with_books():
    with get_connection() as connection:
        connection.executemany("""
        INSERT INTO books (id, title, genre, copies)
        VALUES(?, ?, ?, ?)
        """, books)

        connection.commit()