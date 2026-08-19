from datetime import datetime, timezone
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
# Import all SQLAlchemy models to register them on Base.metadata before create_all
import app.models  # noqa: F401
from app.models.user import User, UserRole
from app.models.setting import Setting
from app.core.security import get_password_hash

logger = logging.getLogger("attendance.init_db")


def init_db(db: Optional[Session] = None) -> None:
    """
    Ensure all database tables exist and seed initial administrator account (Rajavel)
    and configurable system settings without destroying existing data.
    """
    logger.info("Verifying database schema and registering SQLAlchemy models...")
    
    # 1. Ensure all models are registered and create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # 2. Check or create default user 'Rajavelu'
        rajavelu_user = db.query(User).filter(
            (User.username == "Rajavelu") | 
            (User.email == "rajavelu@example.com") |
            (User.email == "rajavelu@attendance.local")
        ).first()
        
        if not rajavelu_user:
            rajavelu_user = User(
                username="Rajavelu",
                full_name="Rajavelu",
                email="rajavelu@gmail.com",
                password_hash=get_password_hash("Rajavelu@123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_email_verified=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(rajavelu_user)
            logger.info("Created default user account (username: Rajavelu, password: Rajavelu@123)")
        else:
            rajavelu_user.username = "Rajavelu"
            rajavelu_user.email = "rajavelu@example.com"
            rajavelu_user.role = UserRole.ADMIN
            rajavelu_user.is_active = True
            rajavelu_user.password_hash = get_password_hash("Rajavelu@123")

        # 3. Check or create Super Admin 'Rajavel'
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
            # Preserve existing admin user and password hash without overwriting
            if not admin_user.is_active or admin_user.role != UserRole.ADMIN:
                admin_user.role = UserRole.ADMIN
                admin_user.is_active = True

        # 3. Check or create Manager account for manager role access
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

        # 4. Seed Configurable System Settings if missing
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
        logger.info("Database startup initialization completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    init_db()
