def test_backup_create_list_and_download(client, admin_headers):
    # 1. List backups (initially empty or existing)
    list_res = client.get("/api/v1/backups", headers=admin_headers)
    assert list_res.status_code == 200

    # 2. Trigger Backup
    create_res = client.post("/api/v1/backups", headers=admin_headers)
    assert create_res.status_code == 201
    backup_id = create_res.json()["data"]["id"]
    assert backup_id.endswith(".db")

    # 3. Download Backup
    download_res = client.get(f"/api/v1/backups/{backup_id}/download", headers=admin_headers)
    assert download_res.status_code == 200
    assert len(download_res.content) > 0


def test_backup_path_traversal_prevention(client, admin_headers):
    # Attempt path traversal
    res = client.get("/api/v1/backups/..%2F..%2Fetc%2Fpasswd/download", headers=admin_headers)
    assert res.status_code in [400, 404]
