from datetime import date
from app.models.department import Department


def _get_or_create_dept(db_session):
    dept = db_session.query(Department).first()
    if not dept:
        dept = Department(name="Engineering", description="Engineering team", is_active=True)
        db_session.add(dept)
        db_session.commit()
    return dept


def test_create_and_get_employee(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)

    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
        "phone": "+1234567890",
        "department_id": dept.id,
        "designation": "Software Engineer",
        "joining_date": str(date.today()),
        "employment_type": "FULL_TIME",
        "status": "ACTIVE"
    }

    res = client.post("/api/v1/employees", json=payload, headers=manager_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["first_name"] == "Alice"
    assert data["full_name"] == "Alice Smith"
    assert data["employee_id"].startswith("EMP-")
    emp_id = data["id"]

    # Fetch employee by ID
    get_res = client.get(f"/api/v1/employees/{emp_id}", headers=manager_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["email"] == "alice.smith@example.com"


def test_duplicate_employee_email_prevention(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)
    payload = {
        "first_name": "Bob",
        "last_name": "Taylor",
        "email": "bob.taylor@example.com",
        "department_id": dept.id,
        "designation": "DevOps Engineer",
        "joining_date": str(date.today()),
        "status": "ACTIVE"
    }
    res1 = client.post("/api/v1/employees", json=payload, headers=manager_headers)
    assert res1.status_code == 201

    # Second creation with same email must fail with 409
    res2 = client.post("/api/v1/employees", json=payload, headers=manager_headers)
    assert res2.status_code == 409


def test_employee_status_update_and_soft_delete(client, manager_headers, db_session):
    dept = _get_or_create_dept(db_session)
    payload = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@example.com",
        "department_id": dept.id,
        "designation": "QA Analyst",
        "joining_date": str(date.today())
    }
    create_res = client.post("/api/v1/employees", json=payload, headers=manager_headers)
    emp_id = create_res.json()["data"]["id"]

    # Update status to ON_NOTICE
    patch_res = client.patch(f"/api/v1/employees/{emp_id}/status", json={
        "status": "ON_NOTICE",
        "reason": "Resignation submitted"
    }, headers=manager_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "ON_NOTICE"

    # Soft delete
    del_res = client.delete(f"/api/v1/employees/{emp_id}", headers=manager_headers)
    assert del_res.status_code == 200

    # Getting deleted employee returns 404
    get_res = client.get(f"/api/v1/employees/{emp_id}", headers=manager_headers)
    assert get_res.status_code == 404
