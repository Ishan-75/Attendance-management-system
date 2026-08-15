from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    employees,
    attendance,
    leaves,
    departments,
    holidays,
    dashboard,
    reports,
    audit,
    backup,
    settings,
    health,
    sync,
    system
)

api_router = APIRouter()

# Health endpoints mounted at root of api_router as well
api_router.include_router(health.router)

# Resource endpoints
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(employees.router)
api_router.include_router(attendance.router)
api_router.include_router(leaves.router)
api_router.include_router(departments.router)
api_router.include_router(holidays.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(audit.router)
api_router.include_router(backup.router)
api_router.include_router(settings.router)
api_router.include_router(sync.router)
api_router.include_router(sync.devices_router)
api_router.include_router(system.router)
