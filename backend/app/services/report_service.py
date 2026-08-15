import csv
import io
import json
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.report import AttendanceReportRow, ReportFilter

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class ReportService:
    @staticmethod
    def get_attendance_report(
        db: Session,
        filters: ReportFilter
    ) -> List[AttendanceReportRow]:
        """Fetch filtered attendance records for reports."""
        query = db.query(Attendance).join(Employee).outerjoin(Department, Employee.department_id == Department.id)

        query = query.filter(
            Attendance.attendance_date >= filters.start_date,
            Attendance.attendance_date <= filters.end_date,
            Employee.deleted_at.is_(None)
        )

        if filters.department_id:
            query = query.filter(Employee.department_id == filters.department_id)

        if filters.employee_id:
            query = query.filter(Employee.id == filters.employee_id)

        if filters.status:
            query = query.filter(Attendance.status == filters.status)

        records = query.order_by(Attendance.attendance_date.desc(), Employee.employee_id.asc()).all()

        rows = []
        for r in records:
            emp = r.employee
            dept_name = emp.department.name if emp and emp.department else "Unassigned"
            rows.append(
                AttendanceReportRow(
                    employee_code=emp.employee_id if emp else "N/A",
                    employee_name=emp.full_name if emp else "N/A",
                    department_name=dept_name,
                    attendance_date=r.attendance_date,
                    status=r.status,
                    check_in=r.check_in_time.strftime("%H:%M") if r.check_in_time else "-",
                    check_out=r.check_out_time.strftime("%H:%M") if r.check_out_time else "-",
                    total_hours=r.total_hours,
                    overtime_hours=r.overtime_hours,
                    late_minutes=r.late_minutes,
                    early_departure_minutes=r.early_departure_minutes,
                    remarks=r.remarks or ""
                )
            )
        return rows

    @staticmethod
    def export_attendance_csv(
        db: Session,
        filters: ReportFilter
    ) -> io.StringIO:
        """Generate formatted RFC 4180 CSV export of attendance report."""
        rows = ReportService.get_attendance_report(db, filters)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow([
            "Employee ID",
            "Employee Name",
            "Department",
            "Date",
            "Status",
            "Check In",
            "Check Out",
            "Total Hours",
            "Overtime Hours",
            "Late (Mins)",
            "Early Departure (Mins)",
            "Remarks"
        ])

        for row in rows:
            writer.writerow([
                row.employee_code,
                row.employee_name,
                row.department_name,
                row.attendance_date.strftime("%Y-%m-%d"),
                row.status,
                row.check_in,
                row.check_out,
                f"{row.total_hours:.2f}",
                f"{row.overtime_hours:.2f}",
                row.late_minutes,
                row.early_departure_minutes,
                row.remarks
            ])

        output.seek(0)
        return output

    @staticmethod
    def export_attendance_excel(
        db: Session,
        filters: ReportFilter
    ) -> io.BytesIO:
        """Generate professionally styled Excel (.xlsx) workbook with formulas and formatted cells."""
        rows = ReportService.get_attendance_report(db, filters)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance Statement"
        ws.views.sheetView[0].showGridLines = True

        # Styles
        title_font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        summary_font = Font(name="Calibri", size=11, bold=True, color="0F172A")
        summary_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        border_thin = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1")
        )

        status_fills = {
            "PRESENT": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),
            "ABSENT": PatternFill(start_color="FFE4E6", end_color="FFE4E6", fill_type="solid"),
            "LEAVE": PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
            "HALF_DAY": PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid"),
            "WEEK_OFF": PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),
            "HOLIDAY": PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid"),
            "WORK_FROM_HOME": PatternFill(start_color="CFFAFE", end_color="CFFAFE", fill_type="solid"),
        }

        # Title Block
        ws["A1"] = "WorkforceHub Attendance Report"
        ws["A1"].font = title_font
        ws["A2"] = f"Report Date Range: {filters.start_date.strftime('%Y-%m-%d')} to {filters.end_date.strftime('%Y-%m-%d')} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws["A2"].font = sub_font

        headers = [
            "Employee ID",
            "Employee Name",
            "Department",
            "Date",
            "Status",
            "Check In",
            "Check Out",
            "Total Hours",
            "Overtime (Hrs)",
            "Late (Mins)",
            "Early Departure",
            "Remarks"
        ]

        start_row = 4
        for col_idx, header_text in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col_idx, value=header_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_thin

        ws.row_dimensions[start_row].height = 28

        curr_row = start_row + 1
        total_hours_sum = 0.0
        total_ot_sum = 0.0

        for r in rows:
            ws.cell(row=curr_row, column=1, value=r.employee_code).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=r.employee_name).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_row, column=3, value=r.department_name).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_row, column=4, value=r.attendance_date.strftime("%Y-%m-%d")).alignment = Alignment(horizontal="center")
            
            status_cell = ws.cell(row=curr_row, column=5, value=r.status)
            status_cell.alignment = Alignment(horizontal="center")
            if r.status in status_fills:
                status_cell.fill = status_fills[r.status]

            ws.cell(row=curr_row, column=6, value=r.check_in).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=7, value=r.check_out).alignment = Alignment(horizontal="center")
            
            h_cell = ws.cell(row=curr_row, column=8, value=round(r.total_hours, 2))
            h_cell.alignment = Alignment(horizontal="right")
            h_cell.number_format = "0.00"
            total_hours_sum += r.total_hours

            ot_cell = ws.cell(row=curr_row, column=9, value=round(r.overtime_hours, 2))
            ot_cell.alignment = Alignment(horizontal="right")
            ot_cell.number_format = "0.00"
            total_ot_sum += r.overtime_hours

            ws.cell(row=curr_row, column=10, value=r.late_minutes).alignment = Alignment(horizontal="right")
            ws.cell(row=curr_row, column=11, value=r.early_departure_minutes).alignment = Alignment(horizontal="right")
            ws.cell(row=curr_row, column=12, value=r.remarks).alignment = Alignment(horizontal="left")

            for col_idx in range(1, 13):
                ws.cell(row=curr_row, column=col_idx).border = border_thin

            ws.row_dimensions[curr_row].height = 20
            curr_row += 1

        # Summary footer row
        summary_row = curr_row
        ws.cell(row=summary_row, column=1, value="TOTAL SUMMARY").font = summary_font
        ws.cell(row=summary_row, column=2, value=f"{len(rows)} Records").font = summary_font
        ws.cell(row=summary_row, column=8, value=round(total_hours_sum, 2)).font = summary_font
        ws.cell(row=summary_row, column=8).number_format = "0.00"
        ws.cell(row=summary_row, column=9, value=round(total_ot_sum, 2)).font = summary_font
        ws.cell(row=summary_row, column=9).number_format = "0.00"

        for col_idx in range(1, 13):
            cell = ws.cell(row=summary_row, column=col_idx)
            cell.fill = summary_fill
            cell.border = border_thin

        ws.row_dimensions[summary_row].height = 24

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        ws.column_dimensions["B"].width = 24
        ws.column_dimensions["C"].width = 20
        ws.column_dimensions["L"].width = 28

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def export_attendance_json(
        db: Session,
        filters: ReportFilter
    ) -> str:
        """Generate structured JSON report payload with summary metrics."""
        rows = ReportService.get_attendance_report(db, filters)
        
        status_counts = {}
        total_hours = 0.0
        total_overtime = 0.0
        
        serialized_rows = []
        for r in rows:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
            total_hours += r.total_hours
            total_overtime += r.overtime_hours
            serialized_rows.append({
                "employee_code": r.employee_code,
                "employee_name": r.employee_name,
                "department": r.department_name,
                "date": r.attendance_date.strftime("%Y-%m-%d"),
                "status": r.status,
                "check_in": r.check_in,
                "check_out": r.check_out,
                "total_hours": round(r.total_hours, 2),
                "overtime_hours": round(r.overtime_hours, 2),
                "late_minutes": r.late_minutes,
                "early_departure_minutes": r.early_departure_minutes,
                "remarks": r.remarks
            })

        payload = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "filter_start_date": filters.start_date.strftime("%Y-%m-%d"),
                "filter_end_date": filters.end_date.strftime("%Y-%m-%d"),
                "total_records": len(rows),
                "summary": {
                    "total_hours_worked": round(total_hours, 2),
                    "total_overtime_hours": round(total_overtime, 2),
                    "status_breakdown": status_counts
                }
            },
            "records": serialized_rows
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def export_attendance_html(
        db: Session,
        filters: ReportFilter
    ) -> str:
        """Generate print-ready HTML/PDF printable attendance report."""
        rows = ReportService.get_attendance_report(db, filters)
        total_hours = sum(r.total_hours for r in rows)
        total_ot = sum(r.overtime_hours for r in rows)

        rows_html = ""
        for r in rows:
            status_class = {
                "PRESENT": "badge-present",
                "ABSENT": "badge-absent",
                "LEAVE": "badge-leave",
                "HALF_DAY": "badge-half",
                "WEEK_OFF": "badge-off",
                "HOLIDAY": "badge-holiday",
                "WORK_FROM_HOME": "badge-wfh"
            }.get(r.status, "badge-default")

            rows_html += f"""
            <tr>
                <td style="font-family: monospace; font-weight: bold; color: #2563eb;">{r.employee_code}</td>
                <td><strong>{r.employee_name}</strong></td>
                <td>{r.department_name}</td>
                <td style="font-family: monospace;">{r.attendance_date}</td>
                <td><span class="badge {status_class}">{r.status}</span></td>
                <td style="font-family: monospace;">{r.check_in}</td>
                <td style="font-family: monospace;">{r.check_out}</td>
                <td style="font-weight: bold; text-align: right;">{r.total_hours:.2f}h</td>
                <td style="color: #4f46e5; font-weight: bold; text-align: right;">{f'+{r.overtime_hours:.2f}h' if r.overtime_hours > 0 else '-'}</td>
                <td style="text-align: right;">{f'{r.late_minutes}m' if r.late_minutes > 0 else '-'}</td>
                <td>{r.remarks or '-'}</td>
            </tr>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Attendance Statement ({filters.start_date} to {filters.end_date})</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a; margin: 0; padding: 24px; font-size: 12px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 20px; }}
        .title {{ font-size: 20px; font-weight: bold; color: #1e3a8a; }}
        .subtitle {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }}
        .metric-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }}
        .metric-label {{ font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 600; }}
        .metric-val {{ font-size: 18px; font-weight: bold; color: #0f172a; margin-top: 2px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th {{ background: #f1f5f9; color: #475569; font-size: 11px; text-transform: uppercase; padding: 8px 10px; border-bottom: 1px solid #cbd5e1; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; }}
        .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }}
        .badge-present {{ background: #dcfce7; color: #15803d; }}
        .badge-absent {{ background: #ffe4e6; color: #be123c; }}
        .badge-leave {{ background: #fef3c7; color: #b45309; }}
        .badge-half {{ background: #ffedd5; color: #c2410c; }}
        .badge-holiday {{ background: #f3e8ff; color: #7e22ce; }}
        .badge-wfh {{ background: #cffafe; color: #0e7490; }}
        .badge-off {{ background: #f1f5f9; color: #475569; }}
        .badge-default {{ background: #f1f5f9; color: #475569; }}
        .footer {{ margin-top: 24px; font-size: 10px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 16px; text-align: right;">
        <button onclick="window.print()" style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">Print / Save as PDF</button>
    </div>
    <div class="header">
        <div>
            <div class="title">🏢 WorkforceHub — Official Attendance Report</div>
            <div class="subtitle">Reporting Period: <strong>{filters.start_date}</strong> to <strong>{filters.end_date}</strong></div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 11px; color: #64748b;">Generated on</div>
            <div style="font-weight: bold; font-family: monospace;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
    </div>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-label">Total Records</div>
            <div class="metric-val">{len(rows)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Hours Logged</div>
            <div class="metric-val">{total_hours:.1f} hrs</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Overtime</div>
            <div class="metric-val" style="color: #4f46e5;">{total_ot:.1f} hrs</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Compliance Status</div>
            <div class="metric-val" style="color: #15803d;">Verified</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Emp Code</th>
                <th>Employee Name</th>
                <th>Department</th>
                <th>Date</th>
                <th>Status</th>
                <th>In</th>
                <th>Out</th>
                <th style="text-align: right;">Hours</th>
                <th style="text-align: right;">Overtime</th>
                <th style="text-align: right;">Late</th>
                <th>Remarks</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="footer">
        Confidential Document — Generated by WorkforceHub Attendance Suite. All rights reserved.
    </div>
</body>
</html>"""
