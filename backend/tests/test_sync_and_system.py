import uuid
from datetime import date
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.holiday import Holiday
from app.models.sync import Device, SyncOperation, SyncConflict
from app.models.attendance import Attendance


def test_initial_admin_is_rajavel(client, db_session):
    admin = db_session.query(User).filter(User.username == "Rajavel").first()
    assert admin is not None
    assert admin.email == "attendancesystem55@gmail.com"
    assert admin.role == UserRole.ADMIN

    # Test login with Rajavel
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "Rajavel",
        "password": "Admin@123456"
    })
    assert res.status_code == 200
    assert res.json()["data"]["user"]["username"] == "Rajavel"


def test_device_registration_and_list(client, admin_headers, db_session):
    dev_id = f"test_dev_{uuid.uuid4().hex[:8]}"
    
    # 1. Register device
    reg_res = client.post("/api/v1/devices/register", json={
        "device_id": dev_id,
        "device_name": "Manager Galaxy Tab S8",
        "platform": "android",
        "app_version": "1.0.0"
    }, headers=admin_headers)
    assert reg_res.status_code == 200
    assert reg_res.json()["data"]["device_id"] == dev_id

    # 2. List devices
    list_res = client.get("/api/v1/devices", headers=admin_headers)
    assert list_res.status_code == 200
    devs = list_res.json()["data"]
    assert any(d["device_id"] == dev_id for d in devs)


def test_sync_push_idempotency(client, manager_headers, db_session):
    # Setup department and employee
    dept = Department(name="Sync Test Dept", is_active=True)
    db_session.add(dept)
    db_session.commit()

    emp_res = client.post("/api/v1/employees", json={
        "first_name": "Offline", "last_name": "Worker", "email": f"sync_{uuid.uuid4().hex[:6]}@example.com",
        "department_id": dept.id, "designation": "Technician", "joining_date": "2026-08-01"
    }, headers=manager_headers)
    emp_id = emp_res.json()["data"]["id"]

    op_id = f"op_{uuid.uuid4().hex}"
    dev_id = f"dev_{uuid.uuid4().hex[:8]}"

    batch_payload = {
        "device_id": dev_id,
        "operations": [
            {
                "operation_id": op_id,
                "entity_type": "Attendance",
                "entity_id": str(emp_id),
                "operation": "CREATE",
                "payload": {
                    "employee_id": emp_id,
                    "attendance_date": "2026-08-10",
                    "status": "PRESENT",
                    "check_in_time": "09:00",
                    "check_out_time": "18:00",
                    "remarks": "Marked offline"
                }
            }
        ]
    }

    # 1. First sync push
    res1 = client.post("/api/v1/sync/push", json=batch_payload, headers=manager_headers)
    assert res1.status_code == 200
    assert res1.json()["data"]["processed"] == 1
    assert res1.json()["data"]["skipped"] == 0

    # 2. Second sync push with same operation_id (must be skipped idempotently)
    res2 = client.post("/api/v1/sync/push", json=batch_payload, headers=manager_headers)
    assert res2.status_code == 200
    assert res2.json()["data"]["processed"] == 0
    assert res2.json()["data"]["skipped"] == 1

    # Verify only 1 attendance record exists via API and DB
    db_session.expire_all()
    count = db_session.query(Attendance).filter(
        Attendance.employee_id == emp_id,
        Attendance.attendance_date == date(2026, 8, 10)
    ).count()
    assert count == 1


def test_sync_conflict_detection_and_resolution(client, manager_headers, db_session):
    dept = Department(name="Conflict Test Dept", is_active=True)
    db_session.add(dept)
    db_session.commit()

    emp_res = client.post("/api/v1/employees", json={
        "first_name": "Conflict", "last_name": "Target", "email": f"conflict_{uuid.uuid4().hex[:6]}@example.com",
        "department_id": dept.id, "designation": "Technician", "joining_date": "2026-08-01"
    }, headers=manager_headers)
    emp_id = emp_res.json()["data"]["id"]

    target_date = "2026-08-12"

    # 1. Server already has attendance marked as PRESENT
    client.post("/api/v1/attendance", json={
        "employee_id": emp_id,
        "attendance_date": target_date,
        "status": "PRESENT",
        "check_in_time": "09:00:00",
        "check_out_time": "18:00:00"
    }, headers=manager_headers)

    # 2. Device B pushes concurrent offline record marked as ABSENT
    dev_b_op = f"op_devb_{uuid.uuid4().hex}"
    push_res = client.post("/api/v1/sync/push", json={
        "device_id": "device_tablet_b",
        "operations": [
            {
                "operation_id": dev_b_op,
                "entity_type": "Attendance",
                "entity_id": str(emp_id),
                "operation": "UPDATE",
                "payload": {
                    "employee_id": emp_id,
                    "attendance_date": target_date,
                    "status": "ABSENT",
                    "remarks": "Reported sick on call"
                }
            }
        ]
    }, headers=manager_headers)
    assert push_res.status_code == 200
    assert push_res.json()["data"]["conflicts"] == 1

    # 3. Check conflicts endpoint
    conflicts_res = client.get("/api/v1/sync/conflicts", headers=manager_headers)
    assert conflicts_res.status_code == 200
    conflicts = conflicts_res.json()["data"]
    assert len(conflicts) >= 1
    conflict_id = conflicts[0]["conflict_id"]

    # 4. Resolve conflict by choosing CLIENT_WINS (accepting the offline ABSENT mark)
    resolve_res = client.post(f"/api/v1/sync/conflicts/{conflict_id}/resolve", json={
        "resolution_strategy": "CLIENT_WINS",
        "resolution_notes": "Manager confirmed employee was indeed absent"
    }, headers=manager_headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["data"]["status"] == "RESOLVED"

    # Verify attendance status is now updated to ABSENT
    att = db_session.query(Attendance).filter(
        Attendance.employee_id == emp_id,
        Attendance.attendance_date == date(2026, 8, 12)
    ).first()
    assert att.status == "ABSENT"


def test_smtp_status_and_test_email(client, admin_headers):
    # 1. Get safe SMTP status
    status_res = client.get("/api/v1/system/smtp-status", headers=admin_headers)
    assert status_res.status_code == 200
    status_data = status_res.json()["data"]
    assert status_data["smtp_host"] == "smtp.gmail.com"
    assert status_data["smtp_port"] == 587
    assert status_data["smtp_username"] == "attendancesystem55@gmail.com"
    # Ensure password is NEVER returned in response
    assert "smtp_password" not in status_data

    # 2. Test email endpoint (safe response format without password disclosure)
    test_res = client.post("/api/v1/system/test-email", json={
        "target_email": "attendancesystem55@gmail.com"
    }, headers=admin_headers)
    assert test_res.status_code == 200
    res_json = test_res.json()
    assert "success" in res_json
    assert "message" in res_json
