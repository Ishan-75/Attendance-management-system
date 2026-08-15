from datetime import date, datetime, timezone
import logging
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.setting import Setting
from app.core.security import get_password_hash

logger = logging.getLogger("attendance.init_db")


def init_db(db: Session) -> None:
    """Seed initial administrator account (Rajavel) and configurable system settings."""
    # 1. Check or create Super Admin 'Rajavel'
    admin_user = db.query(User).filter(
        (User.username == "Rajavel") | (User.email == "attendancesystem55@gmail.com")
    ).first()
    
    if not admin_user:
        admin_user = User(
            username="Rajavel",
            full_name="Rajavel",
            email="attendancesystem55@gmail.com",
            password_hash=get_password_hash("Admin@123456"),
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(admin_user)
        logger.info("Created administrator account (username: Rajavel, email: attendancesystem55@gmail.com)")
    else:
        # Ensure username and email match requested admin identity
        admin_user.username = "Rajavel"
        admin_user.email = "attendancesystem55@gmail.com"
        admin_user.role = UserRole.ADMIN
        admin_user.is_active = True

    # 2. Check or create Manager account for manager role access
    manager_user = db.query(User).filter(User.username == "manager").first()
    if not manager_user:
        manager_user = User(
            username="manager",
            full_name="Operations Manager",
            email="manager@example.com",
            password_hash=get_password_hash("Manager@123456"),
            role=UserRole.MANAGER,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(manager_user)
        logger.info("Created default manager (username: manager, email: manager@example.com)")

    # 3. Seed Configurable System Settings
    default_settings = [
        ("company_name", "WorkforceHub Enterprise", "Company or organization display name"),
        ("shift_start_time", "09:00", "Standard work shift start time (HH:MM)"),
        ("shift_end_time", "18:00", "Standard work shift end time (HH:MM)"),
        ("break_duration_minutes", "60", "Total lunch and break duration in minutes"),
        ("default_working_hours", "8.0", "Expected full-day working hours"),
        ("half_day_hours", "4.0", "Minimum hours required for half-day"),
        ("overtime_threshold_hours", "8.0", "Hours beyond which overtime compensation applies"),
        ("weekly_off_days", "Saturday,Sunday", "Standard weekly off days"),
        ("grace_period_minutes", "15", "Grace period in minutes before marked late"),
        ("admin_notification_email", "attendancesystem55@gmail.com", "Primary admin email for alerts")
    ]

    for key, value, desc in default_settings:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            db.add(Setting(key=key, value=value, description=desc))

    # Note: Departments and Holidays are completely user-customizable and start empty.

    db.commit()
    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
