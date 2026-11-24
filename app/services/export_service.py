import csv
import io
from datetime import date
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.models.attendance import AttendanceLog

class ExportService:
    """Exports attendance logs into CSV or Styled Excel documents."""

    @staticmethod
    def generate_csv(logs: List[AttendanceLog]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Employee ID", "Full Name", "Department", "Date",
            "Check-In", "Check-Out", "Status", "Confidence", "Method"
        ])

        for log in logs:
            emp_id = log.user.employee_id if log.user else "N/A"
            name = log.user.full_name if log.user else "Unknown"
            dept = log.user.department.name if log.user and log.user.department else "General"
            cin = log.check_in.strftime("%H:%M:%S") if log.check_in else "-"
            cout = log.check_out.strftime("%H:%M:%S") if log.check_out else "-"
            writer.writerow([
                log.id, emp_id, name, dept, str(log.log_date),
                cin, cout, log.status, f"{log.match_confidence:.2f}", log.verification_method
            ])

        return output.getvalue()

    @staticmethod
    def generate_excel(logs: List[AttendanceLog]) -> io.BytesIO:
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Records"

        # Theme styling
        header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        border_side = Side(style="thin", color="E5E7EB")
        thin_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

        headers = [
            "Log ID", "Employee ID", "Full Name", "Department", "Date",
            "Check-In", "Check-Out", "Status", "Confidence", "Verification"
        ]
        ws.append(headers)

        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row_idx, log in enumerate(logs, start=2):
            emp_id = log.user.employee_id if log.user else "N/A"
            name = log.user.full_name if log.user else "Unknown"
            dept = log.user.department.name if log.user and log.user.department else "General"
            cin = log.check_in.strftime("%H:%M:%S") if log.check_in else "-"
            cout = log.check_out.strftime("%H:%M:%S") if log.check_out else "-"

            row_data = [
                log.id, emp_id, name, dept, str(log.log_date),
                cin, cout, log.status, f"{log.match_confidence * 100:.1f}%", log.verification_method
            ]
            ws.append(row_data)

            # Row styling
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = regular_font
                cell.border = thin_border
                if col_idx in [1, 5, 6, 7, 8, 9]:
                    cell.alignment = Alignment(horizontal="center")

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        return file_stream

export_service = ExportService()
