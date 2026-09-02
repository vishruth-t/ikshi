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
                ("similarity", "Confidence Score"),
                ("liveness_score", "IR Liveness Score")
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
                        elif key == "liveness_score":
                            if isinstance(val, (int, float)):
                                val = f"{val:.2f} ({int(val * 100)}%)"
                            elif val is None or val == "":
                                val = "N/A"
                        elif key == "marked_at" and "T" in str(val):
                            val = str(val).replace("T", " ")[:19]
                        formatted_row.append(val)
                    writer.writerow(formatted_row)

            logger.info(f"Successfully exported {len(data)} attendance records to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV to {filepath}: {e}")
            return False

    @staticmethod
    def export_to_html(filepath: str, data: List[Dict[str, Any]], title: str = "Attendance Summary Report") -> bool:
        """Export formatted printable HTML/PDF report with CSS styling and analytics summary."""
        if not data:
            return False
        try:
            target_dir = os.path.dirname(os.path.abspath(filepath))
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            total_records = len(data)
            unique_students = len(set(r.get("student_number") for r in data if r.get("student_number")))
            present_count = sum(1 for r in data if r.get("status") == "Present")
            avg_similarity = sum(float(r.get("similarity", 0)) for r in data) / max(1, total_records)

            rows_html = []
            for r in data:
                sim = r.get("similarity", 0.0)
                sim_str = f"{sim:.2f} ({int(sim * 100)}%)" if isinstance(sim, (int, float)) else str(sim)
                liv = r.get("liveness_score")
                liv_str = f"{liv:.2f} ({int(liv * 100)}%)" if isinstance(liv, (int, float)) else "N/A"
                marked = str(r.get("marked_at", "")).replace("T", " ")[:19]

                rows_html.append(f"""
                <tr>
                    <td>{r.get('date', '')}</td>
                    <td><b>{r.get('student_number', '')}</b></td>
                    <td>{r.get('name', '')}</td>
                    <td>{r.get('department', '')}</td>
                    <td>{r.get('year', '')}</td>
                    <td>{r.get('subject', '')}</td>
                    <td>{r.get('class_name', '')}</td>
                    <td>{marked}</td>
                    <td><span class="badge badge-present">{r.get('status', 'Present')}</span></td>
                    <td>{sim_str}</td>
                    <td>{liv_str}</td>
                </tr>
                """)

            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            margin: 0;
            padding: 30px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #30363d;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .title {{ font-size: 24px; font-weight: bold; color: #f0f6fc; margin: 0; }}
        .subtitle {{ font-size: 13px; color: #8b949e; margin-top: 4px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 14px;
        }}
        .stat-label {{ font-size: 11px; color: #8b949e; font-weight: 600; text-transform: uppercase; }}
        .stat-val {{ font-size: 22px; font-weight: bold; color: #f0f6fc; margin-top: 4px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border-radius: 8px;
            overflow: hidden;
            font-size: 12px;
        }}
        th {{
            background-color: #21262d;
            color: #8b949e;
            text-align: left;
            padding: 10px 12px;
            font-weight: 600;
            border-bottom: 1px solid #30363d;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #21262d;
            color: #f0f6fc;
        }}
        tr:hover td {{ background: #1f242c; }}
        .badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-present {{ background: #162b1d; color: #3fb950; border: 1px solid #238636; }}
        @media print {{
            body {{ background: white; color: black; padding: 0; }}
            .header {{ border-bottom: 2px solid #ccc; }}
            .title {{ color: black; }}
            .stat-card {{ border: 1px solid #ccc; background: #f9f9f9; }}
            .stat-val {{ color: black; }}
            table {{ background: white; }}
            th {{ background: #eee; color: black; }}
            td {{ color: black; border-bottom: 1px solid #eee; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 class="title">ikshi • Attendance Report</h1>
            <div class="subtitle">Generated on {os.popen('date').read().strip() or 'Today'}</div>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Verified Records</div>
            <div class="stat-val">{total_records}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Unique Students</div>
            <div class="stat-val">{unique_students}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Attendance Rate</div>
            <div class="stat-val">100%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg Confidence</div>
            <div class="stat-val">{avg_similarity * 100:.1f}%</div>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th>DATE</th>
                <th>STUDENT ID</th>
                <th>STUDENT NAME</th>
                <th>DEPARTMENT</th>
                <th>YEAR</th>
                <th>SUBJECT</th>
                <th>CLASS</th>
                <th>MARKED TIME</th>
                <th>STATUS</th>
                <th>CONFIDENCE</th>
                <th>IR LIVENESS</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
</body>
</html>"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Successfully exported HTML report to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export HTML report to {filepath}: {e}")
            return False

    @staticmethod
    def export_to_excel_xml(filepath: str, data: List[Dict[str, Any]]) -> bool:
        """Export to XML Spreadsheet 2003 (.xls/.xlsx compatible) format with styled columns."""
        if not data:
            return False
        try:
            target_dir = os.path.dirname(os.path.abspath(filepath))
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            xml_rows = []
            for r in data:
                sim = r.get("similarity", 0.0)
                sim_str = f"{sim:.2f} ({int(sim * 100)}%)" if isinstance(sim, (int, float)) else str(sim)
                liv = r.get("liveness_score")
                liv_str = f"{liv:.2f} ({int(liv * 100)}%)" if isinstance(liv, (int, float)) else "N/A"
                marked = str(r.get("marked_at", "")).replace("T", " ")[:19]

                cells = [
                    f'<Cell><Data ss:Type="String">{r.get("date", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("student_number", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("name", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("department", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("year", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("subject", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("class_name", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{marked}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("status", "Present")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{sim_str}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{liv_str}</Data></Cell>',
                ]
                xml_rows.append(f"<Row>{''.join(cells)}</Row>")

            xml_content = f"""<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Worksheet ss:Name="Attendance_Report">
  <Table>
   <Row ss:StyleID="Header">
    <Cell><Data ss:Type="String">Date</Data></Cell>
    <Cell><Data ss:Type="String">Student ID</Data></Cell>
    <Cell><Data ss:Type="String">Student Name</Data></Cell>
    <Cell><Data ss:Type="String">Department</Data></Cell>
    <Cell><Data ss:Type="String">Academic Year</Data></Cell>
    <Cell><Data ss:Type="String">Subject</Data></Cell>
    <Cell><Data ss:Type="String">Class / Section</Data></Cell>
    <Cell><Data ss:Type="String">Marked Time</Data></Cell>
    <Cell><Data ss:Type="String">Status</Data></Cell>
    <Cell><Data ss:Type="String">Confidence Score</Data></Cell>
    <Cell><Data ss:Type="String">IR Liveness Score</Data></Cell>
   </Row>
   {''.join(xml_rows)}
  </Table>
 </Worksheet>
</Workbook>"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml_content)
            logger.info(f"Successfully exported XML spreadsheet to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export XML spreadsheet to {filepath}: {e}")
            return False

    @staticmethod
    def export_audits_to_csv(filepath: str, data: List[Dict[str, Any]]) -> bool:
        """Export security audit records to CSV."""
        if not data:
            return False
        try:
            target_dir = os.path.dirname(os.path.abspath(filepath))
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            headers = ["ID", "Timestamp", "Suspected Student", "Student ID", "Interception Reason", "Liveness Score", "Texture Score", "Reflectance Score", "Entropy Score"]
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for r in data:
                    writer.writerow([
                        r.get("id", ""),
                        r.get("timestamp", ""),
                        r.get("matched_name", "Unknown"),
                        r.get("student_number", "N/A"),
                        r.get("reason", ""),
                        f"{float(r.get('liveness_score', 0.0)):.2f}",
                        f"{float(r.get('texture_score', 0.0)):.2f}",
                        f"{float(r.get('reflectance_score', 0.0)):.2f}",
                        f"{float(r.get('entropy_score', 0.0)):.2f}"
                    ])
            return True
        except Exception as e:
            logger.error(f"Failed to export security audits to CSV: {e}")
            return False

    @staticmethod
    def export_audits_to_excel_xml(filepath: str, data: List[Dict[str, Any]]) -> bool:
        """Export security audits to Excel XML format."""
        if not data:
            return False
        try:
            target_dir = os.path.dirname(os.path.abspath(filepath))
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            xml_rows = []
            for r in data:
                cells = [
                    f'<Cell><Data ss:Type="String">{r.get("id", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("timestamp", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("matched_name", "Unknown")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("student_number", "N/A")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{r.get("reason", "")}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{float(r.get("liveness_score", 0.0)):.2f}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{float(r.get("texture_score", 0.0)):.2f}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{float(r.get("reflectance_score", 0.0)):.2f}</Data></Cell>',
                    f'<Cell><Data ss:Type="String">{float(r.get("entropy_score", 0.0)):.2f}</Data></Cell>',
                ]
                xml_rows.append(f"<Row>{''.join(cells)}</Row>")

            xml_content = f"""<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Worksheet ss:Name="Security_Audits">
  <Table>
   <Row ss:StyleID="Header">
    <Cell><Data ss:Type="String">ID</Data></Cell>
    <Cell><Data ss:Type="String">Timestamp</Data></Cell>
    <Cell><Data ss:Type="String">Suspected Student</Data></Cell>
    <Cell><Data ss:Type="String">Student ID</Data></Cell>
    <Cell><Data ss:Type="String">Interception Reason</Data></Cell>
    <Cell><Data ss:Type="String">Liveness Score</Data></Cell>
    <Cell><Data ss:Type="String">Texture Score</Data></Cell>
    <Cell><Data ss:Type="String">Reflectance Score</Data></Cell>
    <Cell><Data ss:Type="String">Entropy Score</Data></Cell>
   </Row>
   {''.join(xml_rows)}
  </Table>
 </Worksheet>
</Workbook>"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml_content)
            return True
        except Exception as e:
            logger.error(f"Failed to export audits to Excel: {e}")
            return False

