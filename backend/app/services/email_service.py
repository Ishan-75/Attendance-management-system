import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger("attendance.email")


class EmailService:
    @staticmethod
    def get_smtp_status() -> Dict[str, Any]:
        """Returns non-sensitive SMTP configuration summary for admin inspection."""
        is_configured = bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
        return {
            "smtp_host": settings.SMTP_HOST or "Not set",
            "smtp_port": settings.SMTP_PORT,
            "smtp_username": settings.SMTP_USERNAME or "Not set",
            "smtp_from_email": settings.SMTP_FROM_EMAIL or "Not set",
            "use_tls": settings.SMTP_USE_TLS,
            "is_configured": is_configured,
            "password_configured": bool(settings.SMTP_PASSWORD)
        }

    @staticmethod
    def test_smtp_connection(target_email: Optional[str] = None) -> Tuple[bool, str]:
        """
        Connects directly to Gmail SMTP (smtp.gmail.com:587) with STARTTLS,
        authenticates, and sends a real test email with a timestamp.
        Returns (success: bool, message: str) with zero credential leakage.
        """
        if not settings.SMTP_HOST:
            return False, "SMTP_HOST is not configured"
        if not settings.SMTP_USERNAME:
            return False, "SMTP_USERNAME is not configured"
        if not settings.SMTP_PASSWORD:
            return False, "SMTP_PASSWORD is missing in .env or environment variables"

        recipient = target_email or settings.SMTP_USERNAME or "attendancesystem55@gmail.com"
        server_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Attendance Management System - SMTP Test"
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = recipient

            plain_text = f"""Attendance Management System - SMTP Test

SMTP configuration is working correctly.
This is a test email from the Attendance Management System.

Server Timestamp: {server_timestamp}
SMTP Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}
Authenticated User: {settings.SMTP_USERNAME}
"""
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
                <div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 16px;">
                    <h2 style="color: #1e3a8a; margin: 0;">Attendance Management System</h2>
                    <p style="color: #64748b; font-size: 13px; margin: 4px 0 0 0;">Official SMTP Configuration Test</p>
                </div>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                    <strong style="color: #166534; font-size: 14px;">✓ SMTP connection and delivery verified successfully</strong>
                    <p style="color: #15803d; font-size: 13px; margin: 6px 0 0 0;">Your Gmail SMTP server is configured and ready to send email notifications, verification links, and password resets.</p>
                </div>
                <table style="width: 100%; font-size: 12px; color: #334155; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold; width: 140px;">Server Timestamp:</td>
                        <td style="padding: 6px 0; font-family: monospace;">{server_timestamp}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">SMTP Host:</td>
                        <td style="padding: 6px 0;">{settings.SMTP_HOST}:{settings.SMTP_PORT} (STARTTLS)</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Sender Identity:</td>
                        <td style="padding: 6px 0;">{settings.SMTP_FROM_NAME} &lt;{settings.SMTP_FROM_EMAIL}&gt;</td>
                    </tr>
                </table>
                <div style="margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: 11px; color: #94a3b8; text-align: center;">
                    Automated system verification email. Do not reply.
                </div>
            </div>
            """

            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Test email successfully dispatched to {recipient}")
            return True, f"SMTP connection and test email sent successfully to {recipient}"

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication Error: Invalid credentials or Gmail App Password required")
            return False, "SMTP authentication failed. Please verify your Gmail address and 16-character App Password."
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP Connection Error: {e}")
            return False, "Failed to establish TCP connection with SMTP host."
        except Exception as e:
            logger.error(f"SMTP Test Error: {e}")
            return False, f"SMTP error: {type(e).__name__}"

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """Send email via SMTP or fallback in development."""
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.info(f"[DEV EMAIL LOG] To: {to_email} | Subject: {subject}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email

            if plain_text:
                msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email successfully sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    def send_verification_email(cls, to_email: str, username: str, token: str) -> bool:
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Verify Your Account - Attendance Management System"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #2563eb;">Welcome, {username}!</h2>
            <p>Thank you for registering with the Attendance Management System. Please verify your email address by clicking the button below:</p>
            <div style="margin: 24px 0;">
                <a href="{verify_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email Address</a>
            </div>
            <p style="color: #64748b; font-size: 14px;">If you didn't create an account, you can safely ignore this email.</p>
        </div>
        """
        plain = f"Hello {username},\n\nPlease verify your email address by opening the following link:\n{verify_url}"
        return cls.send_email(to_email, subject, html, plain)

    @classmethod
    def send_password_reset_email(cls, to_email: str, username: str, token: str) -> bool:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Password Reset Request - Attendance Management System"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #2563eb;">Password Reset Request</h2>
            <p>Hello {username},</p>
            <p>We received a request to reset your password. Click the button below to set a new password:</p>
            <div style="margin: 24px 0;">
                <a href="{reset_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Reset Password</a>
            </div>
            <p style="color: #ef4444; font-size: 14px;">This link will expire in 30 minutes. If you did not request a password reset, please contact your administrator immediately.</p>
        </div>
        """
        plain = f"Hello {username},\n\nReset your password here:\n{reset_url}\n\nThis link will expire in 30 minutes."
        return cls.send_email(to_email, subject, html, plain)
