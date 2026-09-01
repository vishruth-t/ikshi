import os
import csv
import tempfile
import pytest
from reports.exporter import AttendanceExporter

def test_export_csv_success():
    data = [
        {
            "date": "2026-09-01",
            "subject": "Computer Vision",
            "class_name": "CS-101",
            "student_number": "STU001",
            "name": "Darshan",
            "department": "CS",
            "year": "3rd Year",
            "marked_at": "2026-09-01T10:00:00",
            "status": "Present",
            "similarity": 0.92
        }
    ]

    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)

    try:
        success = AttendanceExporter.export_to_csv(path, data)
        assert success is True
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 1
            assert reader[0]["name"] == "Darshan"
            assert reader[0]["student_number"] == "STU001"
            assert reader[0]["subject"] == "Computer Vision"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_export_csv_empty_data():
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        success = AttendanceExporter.export_to_csv(path, [])
        assert success is False
    finally:
        if os.path.exists(path):
            os.remove(path)
