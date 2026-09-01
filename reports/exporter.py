import csv
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AttendanceExporter:
    @staticmethod
    def export_to_csv(filepath: str, data: List[Dict[str, Any]]) -> bool:
        """
        Export attendance records dictionary list to CSV file with clean headers.
        """
        if not data:
            logger.warning("No attendance data to export.")
            return False

        try:
            target_dir = os.path.dirname(os.path.abspath(filepath))
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            header_mapping = [
                ("date", "Date"),
                ("subject", "Subject"),
                ("class_name", "Class / Section"),
                ("student_number", "Student ID"),
                ("name", "Student Name"),
                ("department", "Department"),
                ("year", "Academic Year"),
                ("marked_at", "Marked Time"),
                ("status", "Status"),
                ("similarity", "Confidence Score")
            ]

            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # Write human-readable column headers
                writer.writerow([label for _, label in header_mapping])
                
                for row in data:
                    formatted_row = []
                    for key, _ in header_mapping:
                        val = row.get(key, "")
                        if key == "similarity" and isinstance(val, (int, float)):
                            val = f"{val:.2f} ({int(val * 100)}%)" if val <= 1.0 else f"{val:.2f}"
                        elif key == "marked_at" and "T" in str(val):
                            val = str(val).replace("T", " ")[:19]
                        formatted_row.append(val)
                    writer.writerow(formatted_row)

            logger.info(f"Successfully exported {len(data)} attendance records to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV to {filepath}: {e}")
            return False

