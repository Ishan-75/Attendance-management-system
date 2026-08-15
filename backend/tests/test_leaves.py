from datetime import date, timedelta
from app.models.department import Department
from app.models.attendance import Attendance, AttendanceStatus


def _get_or_create_dept(db_session):
    dept = db_session.query(Department).first()
    if not dept:
        dept = Department(name="Operations", description="Operations team", is_active=True)
        db_session.add(dept)
        db_session.commit()
    return dept


def test_leave_application_and_approval_flow(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)

    emp_res = client.post("/api/v1/employees", json={
        "first_name": "Emma",
        "last_name": "Watson",
        "email": "emma@example.com",
        "department_id": dept.id,
        "designation": "Analyst",
        "joining_date": str(date.today()),
        "status": "ACTIVE"
    }, headers=manager_headers)
    emp_id = emp_res.json()["data"]["id"]

    start = date(2026, 9, 1)
    end = date(2026, 9, 3)

    # 1. Apply Leave
    leave_res = client.post("/api/v1/leaves", json={
        "employee_id": emp_id,
        "leave_type": "CASUAL",
        "start_date": str(start),
        "end_date": str(end),
        "number_of_days": 3.0,
        "reason": "Family vacation"
    }, headers=manager_headers)
    assert leave_res.status_code == 201
    leave_id = leave_res.json()["data"]["id"]

    # 2. Approve Leave
    approve_res = client.patch(f"/api/v1/leaves/{leave_id}/approve", json={"reason": "Approved"}, headers=manager_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == "APPROVED"

    # 3. Verify attendance records were automatically created with status LEAVE
    att_records = db_session.query(Attendance).filter(
        Attendance.employee_id == emp_id,
        Attendance.attendance_date >= start,
        Attendance.attendance_date <= end
    ).all()
    assert len(att_records) == 3
    for r in att_records:
        assert r.status == AttendanceStatus.LEAVE
        assert r.total_hours == 0.0


def test_leave_rejection(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)
    emp_res = client.post("/api/v1/employees", json={
        "first_name": "Frank", "last_name": "Castle", "email": "frank@example.com",
        "department_id": dept.id, "designation": "Security", "joining_date": str(date.today())
    }, headers=manager_headers)
    emp_id = emp_res.json()["data"]["id"]

    leave_res = client.post("/api/v1/leaves", json={
        "employee_id": emp_id,
        "leave_type": "SICK",
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "number_of_days": 2.0,
        "reason": "Dental surgery"
    }, headers=manager_headers)
    leave_id = leave_res.json()["data"]["id"]

    reject_res = client.patch(f"/api/v1/leaves/{leave_id}/reject", json={"reason": "Critical release on that date"}, headers=manager_headers)
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["status"] == "REJECTED"
