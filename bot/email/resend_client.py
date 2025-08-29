
import logging
import re
from typing import Optional, Dict, Any
import resend

class ResendClient:
    
    def __init__(self, api_key: str, default_from: str = "contact@maximally.in"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.default_from = default_from
        resend.api_key = api_key
        
    async def send_email(self, to: str, subject: str, body: str,
                        from_email: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not self.validate_email(to):
                return {
                    'success': False,
                    'error': f'Invalid recipient email: {to}',
                    'status': 'validation_error'
                }

            from_addr = from_email or self.default_from

            response = resend.Emails.send({
                "from": from_addr,
                "to": [to],
                "subject": subject,
                "html": body
            })

            self.logger.info(f"Email sent successfully to {to}")
            return {
                'success': True,
                'message_id': response.get('id'),
                'status': 'sent'
            }

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'status': 'send_error'
            }
        
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    async def get_api_status(self) -> bool:
        """Check API availability."""
        try:
            response = resend.Domains.list()
            return True
        except Exception as e:
            self.logger.error(f"API status check failed: {str(e)}")
            return False