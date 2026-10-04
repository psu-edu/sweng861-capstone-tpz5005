import pytest
import sqlite3
from datetime import datetime, timezone

# Import the equipment database module
from database import equipment_database


# ==================================================================#
# Setup Environment
# ==================================================================#
@pytest.fixture
#-----------------------------------------------#
def test_db(tmp_path, monkeypatch):
#-----------------------------------------------#
    # Separate database for every test
    db_path = tmp_path / "test_equipment.db"
    
    # Mock the database
    monkeypatch.setattr(equipment_database, "db_name", str(db_path))

    # Initialize the mock database
    equipment_database.init_equipment_db()
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
    assert "equipment" in tables
    assert "equipment_reservations" in tables


#-----------------------------------------------#
def test_insert_and_retrieve_equipment(test_db):
#-----------------------------------------------#
    conn = sqlite3.connect(test_db)
    
    # Manually insert a piece of equipment into database
    conn.execute("""
        INSERT INTO equipment (id, name, type, manufacturer, model, copies)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, "DSLR Camera", "Camera", "Canon", "EOS Rebel T7", 3))
    conn.commit()

    # Retreive the piece of gear we just inserted
    cursor = conn.execute(
        "SELECT name, type, manufacturer, model, copies FROM equipment WHERE id = ?",
        (1,)
    )
    item = cursor.fetchone()
    conn.close()

    # Assert that the retreived equipment matches whats in the database
    assert item == ("DSLR Camera", "Camera", "Canon", "EOS Rebel T7", 3)


#-----------------------------------------------#
def test_get_available_equipment(test_db):
#-----------------------------------------------#
    conn = sqlite3.connect(test_db)
    
    # Insert equipment with 3 copies
    conn.execute("""
        INSERT INTO equipment (id, name, type, manufacturer, model, copies)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, "DSLR Camera", "Camera", "Canon", "EOS Rebel T7", 3))

    # Create one reservation for the camera
    conn.execute("""
        INSERT INTO equipment_reservations
        (equipment_id, reserved_by, reserve_start, reserve_end)
        VALUES (?, ?, ?, ?)
    """, (
        1,
        "student@example.edu",
        "2026-10-04T10:00:00+00:00",
        "2026-10-04T12:00:00+00:00"
    ))
    conn.commit()
    conn.close()

    # Set the time to within the reservation window
    requested_time = datetime.fromisoformat("2026-10-04T11:00:00+00:00")
    available = equipment_database.get_available_equipment(requested_time)

    # Assert that the book is in the reservation list
    assert len(available) == 1

    # Assert that there is one less copy of the camera
    assert available[0]["available_copies"] == 2


#-----------------------------------------------#
def test_reserve_equipment_function(test_db):
#-----------------------------------------------#
    # Insert equipment item first
    conn = sqlite3.connect(test_db)
    conn.execute("""
        INSERT INTO equipment (id, name, type, manufacturer, model, copies)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, "Tripod", "Accessory", "Manfrotto", "Compact Light", 1))
    conn.commit()
    conn.close()

    # Set a reservation time
    start = datetime(2026, 10, 4, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)

    # Mimick a reservation call to the database
    res_id = equipment_database.reserve_equipment(1, "user@example.com", start, end)
    
    # Assert that we have retrieved a reservation id
    assert res_id is not None

    # Test attempting to reserve the same single copy for an overlapping window raises ValueError
    overlap_start = datetime(2026, 10, 4, 11, 0, tzinfo=timezone.utc)
    overlap_end = datetime(2026, 10, 4, 13, 0, tzinfo=timezone.utc)
    
    with pytest.raises(ValueError, match="No copies available"):
        equipment_database.reserve_equipment(1, "other@example.com", overlap_start, overlap_end)