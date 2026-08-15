from datetime import date, time
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.audit_log import AuditLog, AuditAction


def _get_or_create_dept(db_session):
    dept = db_session.query(Department).first()
    if not dept:
        dept = Department(name="Engineering", description="Engineering team", is_active=True)
        db_session.add(dept)
        db_session.commit()
    return dept


def test_attendance_marking_and_corrections(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)

    # Create test employee
    emp_res = client.post("/api/v1/employees", json={
        "first_name": "David",
        "last_name": "Miller",
        "email": "david.miller@example.com",
        "department_id": dept.id,
        "designation": "Backend Engineer",
        "joining_date": str(date.today()),
        "status": "ACTIVE"
    }, headers=manager_headers)
    emp_id = emp_res.json()["data"]["id"]

    today_str = str(date.today())

    # 1. Fetch attendance sheet
    sheet_res = client.get(f"/api/v1/attendance/sheet?date={today_str}", headers=manager_headers)
    assert sheet_res.status_code == 200
    assert len(sheet_res.json()["data"]) >= 1

    # 2. Mark Single Attendance
    mark_res = client.post("/api/v1/attendance", json={
        "employee_id": emp_id,
        "attendance_date": today_str,
        "status": "PRESENT",
        "check_in_time": "09:00:00",
        "check_out_time": "18:00:00",
        "remarks": "On time"
    }, headers=manager_headers)
    assert mark_res.status_code == 200
    att_data = mark_res.json()["data"]
    assert att_data["status"] == "PRESENT"
    assert att_data["total_hours"] == 8.0
    att_id = att_data["id"]

    # 3. Attendance Correction with reason
    correct_res = client.put(f"/api/v1/attendance/{att_id}/correct", json={
        "status": "HALF_DAY",
        "check_in_time": "09:00:00",
        "check_out_time": "13:00:00",
        "remarks": "Doctor appointment",
        "reason": "Employee left after half day for medical reason"
    }, headers=manager_headers)
    assert correct_res.status_code == 200
    assert correct_res.json()["data"]["status"] == "HALF_DAY"

    # Verify audit log was created
    audit = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.ATTENDANCE_CORRECTED,
        AuditLog.entity_id == str(att_id)
    ).first()
    assert audit is not None
    assert "medical reason" in audit.description


def test_bulk_attendance_marking(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)

    # Create two employees
    e1 = client.post("/api/v1/employees", json={
        "first_name": "Bulk1", "last_name": "Emp", "email": "bulk1@example.com",
        "department_id": dept.id, "designation": "Dev", "joining_date": str(date.today())
    }, headers=manager_headers).json()["data"]["id"]

    e2 = client.post("/api/v1/employees", json={
        "first_name": "Bulk2", "last_name": "Emp", "email": "bulk2@example.com",
        "department_id": dept.id, "designation": "Dev", "joining_date": str(date.today())
    }, headers=manager_headers).json()["data"]["id"]

    target_date = "2026-08-01"
    bulk_res = client.post("/api/v1/attendance/bulk", json={
        "attendance_date": target_date,
        "records": [
            {"employee_id": e1, "status": "PRESENT", "check_in_time": "09:00:00", "check_out_time": "18:00:00"},
            {"employee_id": e2, "status": "WORK_FROM_HOME", "check_in_time": "09:00:00", "check_out_time": "18:00:00"}
        ]
    }, headers=manager_headers)
    assert bulk_res.status_code == 200
    assert bulk_res.json()["data"] == 2


def test_employee_monthly_calendar(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)
    e = client.post("/api/v1/employees", json={
        "first_name": "Cal", "last_name": "Emp", "email": "cal@example.com",
        "department_id": dept.id, "designation": "Dev", "joining_date": "2026-01-01"
    }, headers=manager_headers).json()["data"]["id"]

    res = client.get(f"/api/v1/attendance/employee/{e}/calendar?year=2026&month=8", headers=manager_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["year"] == 2026
    assert data["month"] == 8
    assert len(data["calendar_days"]) == 31


def test_reports_multi_format_export(client, manager_headers):
    # Test CSV export
    csv_res = client.get("/api/v1/reports/export-csv?start_date=2026-08-01&end_date=2026-08-31", headers=manager_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Employee ID,Employee Name" in csv_res.text

    # Test Excel (.xlsx) export
    excel_res = client.get("/api/v1/reports/export-excel?start_date=2026-08-01&end_date=2026-08-31", headers=manager_headers)
    assert excel_res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in excel_res.headers["content-type"]
    assert len(excel_res.content) > 1000  # Valid binary excel zip structure

    # Test JSON export
    json_res = client.get("/api/v1/reports/export-json?start_date=2026-08-01&end_date=2026-08-31", headers=manager_headers)
    assert json_res.status_code == 200
    json_data = json_res.json()
    assert "metadata" in json_data
    assert "records" in json_data

    # Test HTML export
    html_res = client.get("/api/v1/reports/export-html?start_date=2026-08-01&end_date=2026-08-31", headers=manager_headers)
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "WorkforceHub" in html_res.text
