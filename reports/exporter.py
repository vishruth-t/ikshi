import csv
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AttendanceExporter:
    @staticmethod
    def export_to_csv(filepath: str, data: List[Dict[str, Any]]) -> bool:
        """
        Export attendance records dictionary list to CSV file.
        """
        if not data:
            logger.warning("No attendance data to export.")
            return False

        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            fieldnames = [
                "date", "subject", "class_name", "student_number", "name",
                "department", "year", "marked_at", "status", "similarity"
            ]

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for row in data:
                    writer.writerow(row)

            logger.info(f"Successfully exported {len(data)} attendance records to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV to {filepath}: {e}")
            return False
