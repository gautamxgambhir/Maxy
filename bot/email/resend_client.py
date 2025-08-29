
import logging
import re
import html
import time
from typing import Optional, Dict, Any
import resend

class ResendClient:

    def __init__(self, api_key: str, default_from: str = "contact@maximally.in"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.default_from = default_from
        resend.api_key = api_key

        # Rate limiting
        self.rate_limit_window = 60  # 1 minute
        self.max_emails_per_window = 10  # 10 emails per minute
        self.sent_emails = []

        # Content validation
        self.max_subject_length = 200
        self.max_body_length = 10000  # 10KB limit
        
    async def send_email(self, to: str, subject: str, body: str,
                         from_email: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.',
                    'status': 'rate_limited'
                }

            # Input validation and sanitization
            validation_result = self._validate_and_sanitize_inputs(to, subject, body, from_email)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'status': 'validation_error'
                }

            to = validation_result['to']
            subject = validation_result['subject']
            body = validation_result['body']
            from_addr = validation_result['from_addr']

            # Send email
            response = resend.Emails.send({
                "from": from_addr,
                "to": [to],
                "subject": subject,
                "html": body
            })

            # Record successful send for rate limiting
            self._record_send()

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
        
    def _check_rate_limit(self) -> bool:
        """Check if email sending is within rate limits."""
        current_time = time.time()

        # Clean old entries
        self.sent_emails = [
            timestamp for timestamp in self.sent_emails
            if current_time - timestamp < self.rate_limit_window
        ]

        # Check if under limit
        return len(self.sent_emails) < self.max_emails_per_window

    def _record_send(self):
        """Record a successful email send for rate limiting."""
        self.sent_emails.append(time.time())

    def _validate_and_sanitize_inputs(self, to: str, subject: str, body: str,
                                    from_email: Optional[str]) -> Dict[str, Any]:
        """Validate and sanitize email inputs."""
        # Validate recipient email
        if not self.validate_email(to):
            return {
                'valid': False,
                'error': f'Invalid recipient email: {to}'
            }

        # Validate and sanitize subject
        if not subject or len(subject.strip()) == 0:
            return {
                'valid': False,
                'error': 'Subject cannot be empty'
            }

        if len(subject) > self.max_subject_length:
            return {
                'valid': False,
                'error': f'Subject too long (max {self.max_subject_length} characters)'
            }

        # Basic XSS protection for subject
        subject = html.escape(subject.strip())

        # Validate and sanitize body
        if not body or len(body.strip()) == 0:
            return {
                'valid': False,
                'error': 'Email body cannot be empty'
            }

        if len(body) > self.max_body_length:
            return {
                'valid': False,
                'error': f'Email body too long (max {self.max_body_length} characters)'
            }

        # For HTML content, we'll trust the template system but add basic sanitization
        # Remove potentially dangerous scripts (basic protection)
        body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.IGNORECASE | re.DOTALL)

        # Validate from email
        from_addr = from_email or self.default_from
        if not self.validate_email(from_addr):
            return {
                'valid': False,
                'error': f'Invalid sender email: {from_addr}'
            }

        return {
            'valid': True,
            'to': to.strip(),
            'subject': subject,
            'body': body,
            'from_addr': from_addr
        }

    def validate_email(self, email: str) -> bool:
        """Validate email format with security checks."""
        if not email or len(email) > 254:  # RFC 5321 limit
            return False

        # More restrictive pattern to prevent potential issues
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
        
    async def get_api_status(self) -> bool:
        """Check API availability."""
        try:
            response = resend.Domains.list()
            return True
        except Exception as e:
            self.logger.error(f"API status check failed: {str(e)}")
            return False