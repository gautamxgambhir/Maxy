
import sqlite3
import logging
import threading
from contextlib import contextmanager
from config import Config
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class EmailDatabase:
    
    def __init__(self):
        self.db_path = Config.EMAIL_DATABASE_PATH
        self.lock = threading.Lock()
        self.setup_database()

    def setup_database(self):
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS email_templates (
                        id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        body TEXT NOT NULL,
                        tone TEXT DEFAULT 'formal',
                        placeholders TEXT DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(category, name)
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS email_logs (
                        id TEXT PRIMARY KEY,
                        template_id TEXT,
                        template_name TEXT NOT NULL,
                        recipient_email_hash TEXT NOT NULL,
                        recipient_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent_by INTEGER NOT NULL,
                        FOREIGN KEY(template_id) REFERENCES email_templates(id)
                    )
                ''')

                conn.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_template_timestamp
                    AFTER UPDATE ON email_templates
                    BEGIN
                        UPDATE email_templates SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = old.id;
                    END
                ''')

                conn.execute('CREATE INDEX IF NOT EXISTS idx_templates_category ON email_templates(category)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_templates_name ON email_templates(name)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_template ON email_logs(template_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_status ON email_logs(status)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_sent_at ON email_logs(sent_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_sent_by ON email_logs(sent_by)')

            logger.info("Email Assistant database setup complete")
        except Exception as e:
            logger.error(f"Email Assistant database setup failed: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        self.lock.acquire()
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")

            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Email database error: {str(e)}")
                raise
            finally:
                conn.close()
        finally:
            self.lock.release()

    def create_template(self, template_id: str, category: str, name: str,
                        subject: str, body: str, tone: str = 'formal',
                        placeholders: str = '[]') -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO email_templates
                    (id, category, name, subject, body, tone, placeholders)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (template_id, category, name, subject, body, tone, placeholders))
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Template already exists: {category}/{name}")
            return False
        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            return False

    def get_template(self, template_id: str) -> Optional[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_templates WHERE id = ?', (template_id,))
            return cursor.fetchone()

    def get_template_by_name(self, category: str, name: str) -> Optional[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM email_templates WHERE category = ? AND name = ?',
                (category, name)
            )
            return cursor.fetchone()

    def get_templates_by_category(self, category: str) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM email_templates WHERE category = ? ORDER BY name',
                (category,)
            )
            return cursor.fetchall()

    def get_all_templates(self) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_templates ORDER BY category, name')
            return cursor.fetchall()

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        if not updates:
            return False
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                set_clauses = []
                values = []
                for key, value in updates.items():
                    if key in ['category', 'name', 'subject', 'body', 'tone', 'placeholders']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if not set_clauses:
                    return False
                
                query = f"UPDATE email_templates SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(template_id)
                
                cursor.execute(query, values)
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update template: {str(e)}")
            return False

    def delete_template(self, template_id: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM email_templates WHERE id = ?', (template_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            return False

    def log_email(self, log_id: str, template_id: Optional[str], template_name: str,
                  recipient_email_hash: str, recipient_name: str, status: str,
                  sent_by: int, error_message: Optional[str] = None) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO email_logs
                    (id, template_id, template_name, recipient_email_hash,
                     recipient_name, status, error_message, sent_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (log_id, template_id, template_name, recipient_email_hash,
                      recipient_name, status, error_message, sent_by))
                return True
        except Exception as e:
            logger.error(f"Failed to log email: {str(e)}")
            return False

    def get_email_logs(self, limit: int = 100, offset: int = 0,
                       status_filter: Optional[str] = None,
                       sent_by_filter: Optional[int] = None) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM email_logs WHERE 1=1"
            params = []

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)

            if sent_by_filter:
                query += " AND sent_by = ?"
                params.append(sent_by_filter)

            query += " ORDER BY sent_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return cursor.fetchall()

    def get_email_stats(self) -> Dict[str, Any]:
        """Get email sending statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM email_logs")
            total_emails = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM email_logs WHERE status = 'sent'")
            successful_emails = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT template_name, COUNT(*) as usage_count
                FROM email_logs
                GROUP BY template_name
                ORDER BY usage_count DESC
                LIMIT 5
            ''')
            popular_templates = cursor.fetchall()
            
            cursor.execute('''
                SELECT COUNT(*) FROM email_logs
                WHERE sent_at >= datetime('now', '-7 days')
            ''')
            recent_activity = cursor.fetchone()[0]
            
            return {
                'total_emails': total_emails,
                'successful_emails': successful_emails,
                'success_rate': (successful_emails / total_emails * 100) if total_emails > 0 else 0,
                'popular_templates': [dict(row) for row in popular_templates],
                'recent_activity': recent_activity
            }

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM email_logs
                    WHERE sent_at < datetime('now', '-{} days')
                '''.format(days_to_keep))
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")
            return 0


email_db = EmailDatabase()