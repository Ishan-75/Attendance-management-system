def test_rbac_manager_cannot_access_backups(client, manager_headers):
    # Manager role must be rejected with 403 on Admin routes
    res = client.get("/api/v1/backups", headers=manager_headers)
    assert res.status_code == 403


def test_rbac_manager_cannot_access_audit_logs(client, manager_headers):
    res = client.get("/api/v1/audit-logs", headers=manager_headers)
    assert res.status_code == 403


def test_health_and_readiness_endpoints(client):
    # Liveness check
    liveness = client.get("/api/v1/health")
    assert liveness.status_code == 200
    assert liveness.json()["status"] == "ok"

    # Readiness check
    readiness = client.get("/api/v1/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["database"] == "connected"


def test_unauthenticated_request_rejected(client):
    res = client.get("/api/v1/employees")
    assert res.status_code == 401
    assert "token is missing" in res.json()["message"].lower()


def test_manager_can_manage_holidays(client, manager_headers):
    # Create holiday as manager
    res = client.post("/api/v1/holidays", json={
        "name": "Manager Added Holiday",
        "date": "2026-11-20",
        "description": "Added by manager test",
        "is_active": True
    }, headers=manager_headers)
    assert res.status_code == 201
    hol_id = res.json()["data"]["id"]

    # Update holiday as manager
    upd = client.put(f"/api/v1/holidays/{hol_id}", json={
        "name": "Manager Renamed Holiday"
    }, headers=manager_headers)
    assert upd.status_code == 200
    assert upd.json()["data"]["name"] == "Manager Renamed Holiday"

    # Delete holiday as manager
    del_res = client.delete(f"/api/v1/holidays/{hol_id}", headers=manager_headers)
    assert del_res.status_code == 200


def test_manager_can_manage_departments(client, manager_headers):
    # Create department as manager
    res = client.post("/api/v1/departments", json={
        "name": "New Manager Dept",
        "description": "Created by manager",
        "is_active": True
    }, headers=manager_headers)
    assert res.status_code == 201
    dept_id = res.json()["data"]["id"]

    # Update department as manager
    upd = client.put(f"/api/v1/departments/{dept_id}", json={
        "description": "Updated description"
    }, headers=manager_headers)
    assert upd.status_code == 200
    assert upd.json()["data"]["description"] == "Updated description"

    # Delete department as manager
    del_res = client.delete(f"/api/v1/departments/{dept_id}", headers=manager_headers)
    assert del_res.status_code == 200
