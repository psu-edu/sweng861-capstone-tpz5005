import pytest
import sqlite3
from datetime import datetime, timezone

from database import book_database

# ==================================================================#
# Setup Environment
# ==================================================================#
@pytest.fixture
#-----------------------------------------------#
def test_db(tmp_path, monkeypatch):
#-----------------------------------------------#
    
    # Separate database for every test
    db_path = tmp_path / "test_books.db"
    
    # Mock the database
    monkeypatch.setattr(book_database, "db_name", str(db_path))

    # Initialize the mock database
    book_database.init_book_db()
    return db_path

# ==================================================================#
# Database Tests
# ==================================================================#
#-----------------------------------------------#
def test_database_initialization(test_db):
#-----------------------------------------------#
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Query to see if tables were created
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
    """)
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    # Assert we have data
    assert "books" in tables
    assert "reservations" in tables


#-----------------------------------------------#
def test_insert_and_retrieve_book(test_db):
#-----------------------------------------------#
    conn = sqlite3.connect(test_db)

    # Manually insert book into database
    conn.execute("""
        INSERT INTO books (id, title, genre, copies)
        VALUES (?, ?, ?, ?)
    """, (1, "The Hobbit", "Fantasy", 3))
    conn.commit()

    # Retreive the book we just inserted
    cursor = conn.execute(
        "SELECT title, genre, copies FROM books WHERE id = ?",
        (1,)
    )
    book = cursor.fetchone()
    conn.close()

    # Assert that the retreived book matches whats in the database
    assert book == ("The Hobbit", "Fantasy", 3)


#-----------------------------------------------#
def test_get_available_books(test_db):
#-----------------------------------------------#
    conn = sqlite3.connect(test_db)
    
    # Insert the hobbit with 3 copies
    conn.execute("""
        INSERT INTO books (id, title, genre, copies)
        VALUES (?, ?, ?, ?)
    """, (1, "The Hobbit", "Fantasy", 3))

    # Reserve 1 copy of the hobbit
    conn.execute("""
        INSERT INTO reservations
        (book_id, reserved_by, reserve_start, reserve_end)
        VALUES (?, ?, ?, ?)
    """, (
        1,
        "test_user",
        "2026-10-04T10:00:00+00:00",
        "2026-10-04T12:00:00+00:00"
    ))
    conn.commit()
    conn.close()

    # Set the time to within the reservation window
    requested_time = datetime.fromisoformat("2026-10-04T11:00:00+00:00")
    available = book_database.get_available_books(requested_time)

    # Assert that the book is in the reservation list
    assert len(available) == 1

    # Assert that there is one less copy of the hobbit
    assert available[0]["available_copies"] == 2