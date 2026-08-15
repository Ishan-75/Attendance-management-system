from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIResponse
from app.services.sync_service import SyncService
from app.api.v1.deps import require_manager, require_admin, get_client_ip
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["Synchronization & Offline"])


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str
    platform: str = "android"
    app_version: Optional[str] = "1.0.0"


class SyncPushRequest(BaseModel):
    device_id: str
    operations: List[Dict[str, Any]]


class ConflictResolveRequest(BaseModel):
    resolution_strategy: str  # SERVER_WINS, CLIENT_WINS, MANUAL_MERGE
    resolution_notes: Optional[str] = ""


@router.post("/push", response_model=APIResponse[Dict[str, Any]])
def push_offline_sync(
    request: Request,
    payload: SyncPushRequest,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Idempotently ingests batch offline operations from web/android client.
    Detects and isolates conflicts without silent data destruction.
    """
    ip = get_client_ip(request)
    result = SyncService.push_sync_batch(
        db,
        device_id=payload.device_id,
        operations=payload.operations,
        user=user,
        ip_address=ip
    )
    return APIResponse(
        success=True,
        message=f"Synced {result['processed']} operations ({result['conflicts']} conflicts, {result['skipped']} skipped)",
        data=result
    )


@router.get("/pull", response_model=APIResponse[Dict[str, Any]])
def pull_server_deltas(
    since: Optional[str] = Query(None),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Returns server records and delta changes for local offline cache hydration.
    """
    data = SyncService.pull_server_deltas(db, since_timestamp=since)
    return APIResponse(
        success=True,
        message="Master sync delta retrieved",
        data=data
    )


@router.get("/conflicts", response_model=APIResponse[List[Dict[str, Any]]])
def get_pending_conflicts(
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Returns list of pending conflicts for manual authorized resolution."""
    conflicts = SyncService.get_pending_conflicts(db)
    items = []
    for c in conflicts:
        items.append({
            "id": c.id,
            "conflict_id": c.conflict_id,
            "entity_type": c.entity_type,
            "entity_id": c.entity_id,
            "device_id": c.device_id,
            "server_payload": c.server_payload,
            "client_payload": c.client_payload,
            "conflict_reason": c.conflict_reason,
            "status": c.status,
            "created_at": c.created_at.isoformat()
        })
    return APIResponse(
        success=True,
        message=f"Found {len(items)} pending conflicts",
        data=items
    )


@router.post("/conflicts/{conflict_id}/resolve", response_model=APIResponse[Dict[str, Any]])
def resolve_conflict(
    request: Request,
    conflict_id: str,
    payload: ConflictResolveRequest,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Resolve conflict by choosing SERVER_WINS, CLIENT_WINS, or MANUAL_MERGE."""
    ip = get_client_ip(request)
    resolved = SyncService.resolve_conflict(
        db,
        conflict_id=conflict_id,
        resolution_strategy=payload.resolution_strategy,
        resolution_notes=payload.resolution_notes or "",
        user=user,
        ip_address=ip
    )
    return APIResponse(
        success=True,
        message=f"Conflict resolved with {payload.resolution_strategy}",
        data={"conflict_id": resolved.conflict_id, "status": resolved.status}
    )


# Device Registration Endpoints
devices_router = APIRouter(prefix="/devices", tags=["Device Management"])


@devices_router.post("/register", response_model=APIResponse[Dict[str, Any]])
def register_device(
    payload: DeviceRegisterRequest,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Register or update device heartbeat."""
    dev = SyncService.register_or_heartbeat_device(
        db,
        device_id=payload.device_id,
        device_name=payload.device_name,
        platform=payload.platform,
        app_version=payload.app_version,
        user=user
    )
    return APIResponse(
        success=True,
        message="Device registered successfully",
        data={
            "device_id": dev.device_id,
            "device_name": dev.device_name,
            "platform": dev.platform,
            "last_sync_at": dev.last_sync_at.isoformat() if dev.last_sync_at else None
        }
    )


@devices_router.get("", response_model=APIResponse[List[Dict[str, Any]]])
def get_devices(
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """List all registered devices (Admin / Manager)."""
    devices = SyncService.get_registered_devices(db)
    return APIResponse(
        success=True,
        message="Devices list retrieved",
        data=[
            {
                "id": d.id,
                "device_id": d.device_id,
                "device_name": d.device_name,
                "platform": d.platform,
                "app_version": d.app_version,
                "last_sync_at": d.last_sync_at.isoformat() if d.last_sync_at else None,
                "is_active": d.is_active,
                "created_at": d.created_at.isoformat()
            }
            for d in devices
        ]
    )
