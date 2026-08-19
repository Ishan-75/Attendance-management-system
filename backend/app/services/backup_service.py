import os
import shutil
import sqlite3
import re
from datetime import datetime, timezone
from typing import List, Optional, Any
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.models.user import User
from app.models.audit_log import AuditAction
from app.schemas.backup import BackupMetadata
from app.services.audit_service import AuditService
from app.db.session import RESOLVED_DATABASE_URL, is_mysql, is_sqlite, engine


class BaseBackupService(ABC):
    @abstractmethod
    def create_backup(self, db: Session, user: User, ip_address: Optional[str] = None) -> BackupMetadata:
        pass

    @abstractmethod
    def list_backups(self) -> List[BackupMetadata]:
        pass

    @abstractmethod
    def get_backup_path(self, backup_id: str) -> str:
        pass

    @abstractmethod
    def restore_backup(self, db: Session, backup_id: str, user: User, ip_address: Optional[str] = None) -> bool:
        pass


class SQLiteBackupService(BaseBackupService):
    def __init__(self):
        self.backup_dir = settings.BACKUP_DIR
        os.makedirs(self.backup_dir, exist_ok=True)
        self.db_path = RESOLVED_DATABASE_URL.replace("sqlite:///", "")

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _sanitize_id(self, backup_id: str) -> str:
        clean_id = os.path.basename(backup_id)
        if not re.match(r"^[\w\-. ]+$", clean_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid backup file name")
        return clean_id

    def list_backups(self) -> List[BackupMetadata]:
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups

        for f in os.listdir(self.backup_dir):
            if f.endswith(".db") or f.endswith(".sqlite"):
                full_path = os.path.join(self.backup_dir, f)
                stat = os.stat(full_path)
                backups.append(
                    BackupMetadata(
                        id=f,
                        filename=f,
                        size_bytes=stat.st_size,
                        size_human=self._format_size(stat.st_size),
                        created_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                        creator_name="Admin",
                        db_type="sqlite"
                    )
                )
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups

    def get_backup_path(self, backup_id: str) -> str:
        clean_id = self._sanitize_id(backup_id)
        target_path = os.path.abspath(os.path.join(self.backup_dir, clean_id))
        
        if not target_path.startswith(os.path.abspath(self.backup_dir)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Access denied")

        if not os.path.exists(target_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")

        return target_path

    def create_backup(self, db: Session, user: User, ip_address: Optional[str] = None) -> BackupMetadata:
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_filename = f"attendance_backup_{timestamp_str}.db"
        target_path = os.path.join(self.backup_dir, backup_filename)

        try:
            raw_conn = db.connection().connection.driver_connection
            dst_conn = sqlite3.connect(target_path)
            with dst_conn:
                raw_conn.backup(dst_conn)
            dst_conn.close()

            stat = os.stat(target_path)
            meta = BackupMetadata(
                id=backup_filename,
                filename=backup_filename,
                size_bytes=stat.st_size,
                size_human=self._format_size(stat.st_size),
                created_at=datetime.now(timezone.utc),
                creator_name=user.full_name,
                db_type="sqlite"
            )

            AuditService.log(
                db,
                action=AuditAction.BACKUP_CREATED,
                description=f"Created SQLite database backup: {backup_filename} ({meta.size_human})",
                user_id=user.id,
                entity_type="Backup",
                entity_id=backup_filename,
                new_value={"filename": backup_filename, "size": stat.st_size},
                ip_address=ip_address
            )
            db.commit()
            return meta
        except Exception as e:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create SQLite backup: {str(e)}"
            )

    def restore_backup(self, db: Session, backup_id: str, user: User, ip_address: Optional[str] = None) -> bool:
        backup_path = self.get_backup_path(backup_id)

        # 1. Validate that backup_path is a valid SQLite DB
        try:
            test_conn = sqlite3.connect(backup_path)
            test_cursor = test_conn.cursor()
            test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in test_cursor.fetchall()]
            test_conn.close()

            if "users" not in tables or "attendance" not in tables:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The selected backup file does not contain valid attendance system tables."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted backup file: {str(e)}"
            )

        # 2. Create pre-restore safety backup
        safety_name = f"safety_pre_restore_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.db"
        safety_path = os.path.join(self.backup_dir, safety_name)
        try:
            raw_conn = db.connection().connection.driver_connection
            dst_conn = sqlite3.connect(safety_path)
            with dst_conn:
                raw_conn.backup(dst_conn)
            dst_conn.close()
        except Exception:
            pass

        # 3. Perform atomic restore using sqlite backup onto active raw connection
        try:
            src_conn = sqlite3.connect(backup_path)
            raw_conn = db.connection().connection.driver_connection
            src_conn.backup(raw_conn)
            src_conn.close()

            AuditService.log(
                db,
                action=AuditAction.BACKUP_RESTORED,
                description=f"Restored database from backup {backup_id}. Pre-restore safety backup saved as {safety_name}",
                user_id=user.id,
                entity_type="Backup",
                entity_id=backup_id,
                ip_address=ip_address
            )
            db.commit()
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restore database: {str(e)}"
            )


class MySQLBackupService(BaseBackupService):
    """
    Pure-Python MySQL / Oracle Cloud MySQL backup service.
    Generates standard valid .sql database dump files containing full schema and data
    without requiring external 'mysqldump' binary installed in the container.
    """
    def __init__(self):
        self.backup_dir = settings.BACKUP_DIR
        os.makedirs(self.backup_dir, exist_ok=True)

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _sanitize_id(self, backup_id: str) -> str:
        clean_id = os.path.basename(backup_id)
        if not re.match(r"^[\w\-. ]+$", clean_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid backup file name")
        return clean_id

    def list_backups(self) -> List[BackupMetadata]:
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups

        for f in os.listdir(self.backup_dir):
            if f.endswith(".sql") or f.endswith(".db"):
                full_path = os.path.join(self.backup_dir, f)
                stat = os.stat(full_path)
                backups.append(
                    BackupMetadata(
                        id=f,
                        filename=f,
                        size_bytes=stat.st_size,
                        size_human=self._format_size(stat.st_size),
                        created_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                        creator_name="Admin",
                        db_type="mysql" if f.endswith(".sql") else "sqlite"
                    )
                )
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups

    def get_backup_path(self, backup_id: str) -> str:
        clean_id = self._sanitize_id(backup_id)
        target_path = os.path.abspath(os.path.join(self.backup_dir, clean_id))

        if not target_path.startswith(os.path.abspath(self.backup_dir)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Access denied")

        if not os.path.exists(target_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")

        return target_path

    def _escape_sql_value(self, val: Any) -> str:
        if val is None:
            return "NULL"
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, bool):
            return "1" if val else "0"
        elif isinstance(val, (datetime, )):
            return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            s = str(val).replace("\\", "\\\\").replace("'", "\\'")
            return f"'{s}'"

    def create_backup(self, db: Session, user: User, ip_address: Optional[str] = None) -> BackupMetadata:
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_filename = f"attendance_backup_{timestamp_str}.sql"
        target_path = os.path.join(self.backup_dir, backup_filename)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(f"-- --------------------------------------------------------\n")
                f.write(f"-- WorkforceHub Attendance Management System Database Backup\n")
                f.write(f"-- Central Database: Oracle Cloud MySQL HeatWave / MySQL\n")
                f.write(f"-- Created by: {user.full_name} ({user.username})\n")
                f.write(f"-- Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"-- --------------------------------------------------------\n\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n")
                f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n\n")

                # Query all tables in the current MySQL schema
                tables_res = db.execute(text("SHOW TABLES;")).fetchall()
                table_names = [row[0] for row in tables_res]

                for table in table_names:
                    f.write(f"-- --------------------------------------------------------\n")
                    f.write(f"-- Table structure for `{table}`\n")
                    f.write(f"-- --------------------------------------------------------\n")
                    f.write(f"DROP TABLE IF EXISTS `{table}`;\n")

                    create_res = db.execute(text(f"SHOW CREATE TABLE `{table}`;")).fetchone()
                    if create_res and len(create_res) > 1:
                        f.write(f"{create_res[1]};\n\n")

                    # Fetch rows
                    rows = db.execute(text(f"SELECT * FROM `{table}`;")).fetchall()
                    if rows:
                        f.write(f"-- Dumping data for table `{table}` ({len(rows)} records)\n")
                        f.write(f"LOCK TABLES `{table}` WRITE;\n")
                        for r in rows:
                            vals_str = ", ".join(self._escape_sql_value(v) for v in r)
                            f.write(f"INSERT INTO `{table}` VALUES ({vals_str});\n")
                        f.write(f"UNLOCK TABLES;\n\n")

                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
                f.write("-- Dump completed successfully.\n")

            stat = os.stat(target_path)
            meta = BackupMetadata(
                id=backup_filename,
                filename=backup_filename,
                size_bytes=stat.st_size,
                size_human=self._format_size(stat.st_size),
                created_at=datetime.now(timezone.utc),
                creator_name=user.full_name,
                db_type="mysql"
            )

            AuditService.log(
                db,
                action=AuditAction.BACKUP_CREATED,
                description=f"Created MySQL database backup: {backup_filename} ({meta.size_human})",
                user_id=user.id,
                entity_type="Backup",
                entity_id=backup_filename,
                new_value={"filename": backup_filename, "size": stat.st_size},
                ip_address=ip_address
            )
            db.commit()
            return meta
        except Exception as e:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create MySQL backup: {str(e)}"
            )

    def restore_backup(self, db: Session, backup_id: str, user: User, ip_address: Optional[str] = None) -> bool:
        backup_path = self.get_backup_path(backup_id)

        # 1. Take safety pre-restore backup first
        try:
            self.create_backup(db, user, ip_address=ip_address)
        except Exception:
            pass

        # 2. Execute SQL statements from backup file
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Split statements by semicolon (ignoring comments)
            statements = []
            for stmt in sql_content.split(";"):
                cleaned = stmt.strip()
                if cleaned and not cleaned.startswith("--"):
                    statements.append(cleaned)

            db.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
            for stmt in statements:
                db.execute(text(stmt))
            db.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

            AuditService.log(
                db,
                action=AuditAction.BACKUP_RESTORED,
                description=f"Restored MySQL database from backup {backup_id}.",
                user_id=user.id,
                entity_type="Backup",
                entity_id=backup_id,
                ip_address=ip_address
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restore MySQL database from {backup_id}: {str(e)}"
            )


def get_backup_service() -> BaseBackupService:
    if is_mysql:
        return MySQLBackupService()
    return SQLiteBackupService()
