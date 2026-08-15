from typing import List
from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.backup import BackupMetadata, BackupRestoreRequest
from app.schemas.common import APIResponse
from app.services.backup_service import get_backup_service
from app.api.v1.deps import require_admin, get_client_ip
from app.models.user import User

router = APIRouter(prefix="/backups", tags=["Backup & Restore (Admin)"])


@router.get("", response_model=APIResponse[List[BackupMetadata]])
def list_backups(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_backup_service()
    backups = service.list_backups()
    return APIResponse(
        success=True,
        message="Backups retrieved",
        data=backups
    )


@router.post("", response_model=APIResponse[BackupMetadata], status_code=status.HTTP_201_CREATED)
def create_backup(
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    service = get_backup_service()
    meta = service.create_backup(db, admin, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Database backup created: {meta.filename}",
        data=meta
    )


@router.get("/{backup_id}/download")
def download_backup(
    backup_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_backup_service()
    path = service.get_backup_path(backup_id)
    return FileResponse(
        path=path,
        media_type="application/octet-stream",
        filename=backup_id
    )


@router.post("/{backup_id}/restore", response_model=APIResponse[bool])
def restore_backup(
    request: Request,
    backup_id: str,
    restore_req: BackupRestoreRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if not restore_req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must set confirm=true to proceed with database restore."
        )

    ip = get_client_ip(request)
    service = get_backup_service()
    service.restore_backup(db, backup_id, admin, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Database successfully restored from {backup_id}. A safety snapshot was taken.",
        data=True
    )
