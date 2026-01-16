"""
Email sender module.
Sends daily reports via SMTP with dry-run support.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends reports via SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_pass: str,
        from_addr: str,
        to_addr: str,
        dry_run: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.dry_run = dry_run

    def send_report(
        self,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """
        Send email report.

        Args:
            subject: Email subject line
            body_text: Plain text body
            body_html: Optional HTML body

        Returns:
            True if sent successfully (or dry-run), False otherwise
        """
        if self.dry_run:
            return self._dry_run_send(subject, body_text)

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_addr
            msg['To'] = self.to_addr

            # Attach text part
            text_part = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(text_part)

            # Attach HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(html_part)

            # Send via SMTP
            logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")

            # Try TLS first, fall back to SSL if needed
            try:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
                server.starttls()
            except Exception as e:
                logger.warning(f"STARTTLS failed, trying SSL: {str(e)}")
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30)

            # Login
            logger.info(f"Logging in as {self.smtp_user}...")
            server.login(self.smtp_user, self.smtp_pass)

            # Send
            logger.info(f"Sending email to {self.to_addr}...")
            server.send_message(msg)
            server.quit()

            logger.info("✅ Email sent successfully!")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed: {str(e)}")
            logger.error("Check your SMTP_USER and SMTP_PASS in .env")
            return False

        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {str(e)}")
            return False

    def _dry_run_send(self, subject: str, body_text: str) -> bool:
        """Simulate sending email (dry-run mode)."""
        logger.info("=" * 80)
        logger.info("DRY-RUN MODE: Email not actually sent")
        logger.info("=" * 80)
        logger.info(f"From: {self.from_addr}")
        logger.info(f"To: {self.to_addr}")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 80)
        logger.info("Body Preview (first 500 chars):")
        logger.info("-" * 80)
        logger.info(body_text[:500])
        if len(body_text) > 500:
            logger.info("... (truncated)")
        logger.info("=" * 80)
        logger.info("To send for real, set DRY_RUN=0 in .env")
        logger.info("=" * 80)
        return True

    @staticmethod
    def validate_config(config: dict) -> bool:
        """
        Validate email configuration.

        Args:
            config: Dict with SMTP settings

        Returns:
            True if valid, False otherwise
        """
        required = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass', 'from_addr', 'to_addr']
        missing = [key for key in required if not config.get(key)]

        if missing:
            logger.error(f"Missing email configuration: {', '.join(missing)}")
            logger.error("Please check your .env file")
            return False

        return True
