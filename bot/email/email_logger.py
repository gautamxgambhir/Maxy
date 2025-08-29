
import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import EmailLog

class EmailLogger:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        from .database import email_db
        self.db = email_db
        
    def hash_email(self, email: str) -> str:
        return hashlib.sha256(email.encode()).hexdigest()
        
    async def log_email(self, template_id: str, template_name: str,
                        recipient_email: str, recipient_name: str,
                        status: str, sent_by: int,
                        error_message: Optional[str] = None) -> EmailLog:
        """Record email sending."""
        try:
            import uuid
            log_id = str(uuid.uuid4())

            success = self.db.log_email(
                log_id=log_id,
                template_id=template_id,
                template_name=template_name,
                recipient_email_hash=self.hash_email(recipient_email),
                recipient_name=recipient_name,
                status=status,
                sent_by=sent_by,
                error_message=error_message
            )

            if success:
                email_log = EmailLog(
                    id=log_id,
                    template_id=template_id,
                    template_name=template_name,
                    recipient_email_hash=self.hash_email(recipient_email),
                    recipient_name=recipient_name,
                    status=status,
                    error_message=error_message,
                    sent_by=sent_by
                )
                self.logger.info(f"Email logged: {template_name} -> {recipient_name}")
                return email_log
            else:
                self.logger.error("Failed to log email to database")
                return None

        except Exception as e:
            self.logger.error(f"Failed to log email: {str(e)}")
            return None
        
    async def get_logs(self, filters: Optional[Dict[str, Any]] = None) -> List[EmailLog]:
        """Retrieve email history."""
        try:
            limit = filters.get('limit', 100) if filters else 100
            offset = filters.get('offset', 0) if filters else 0
            status_filter = filters.get('status') if filters else None
            sent_by_filter = filters.get('sent_by') if filters else None

            rows = self.db.get_email_logs(
                limit=limit,
                offset=offset,
                status_filter=status_filter,
                sent_by_filter=sent_by_filter
            )

            return [EmailLog.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get email logs: {str(e)}")
            return []
        
    async def get_stats(self) -> Dict[str, Any]:
        """Generate sending statistics."""
        try:
            return self.db.get_email_stats()
        except Exception as e:
            self.logger.error(f"Failed to get email stats: {str(e)}")
            return {
                'total_emails': 0,
                'successful_emails': 0,
                'success_rate': 0,
                'popular_templates': [],
                'recent_activity': 0
            }