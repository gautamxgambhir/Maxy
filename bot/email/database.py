import os
import sqlite3
import psycopg2
import psycopg2.extras
import logging
import threading
from contextlib import contextmanager
from config import Config
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class EmailDatabase:
    def __init__(self):
        self.lock = threading.Lock()
        self.database_url = Config.EMAIL_DATABASE_URL
        if self.database_url:
            self.mode = "postgres"
        else:
            self.mode = "sqlite"
            self.db_path = Config.EMAIL_DATABASE_PATH
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.setup_database()

    @contextmanager
    def get_connection(self):
        self.lock.acquire()
        conn = None
        try:
            if self.mode == "postgres":
                conn = psycopg2.connect(self.database_url, sslmode="require")
                conn.autocommit = True
            else:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        finally:
            if conn is not None:
                conn.close()
            self.lock.release()

    def setup_database(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) if self.mode == "postgres" else conn.cursor()

                cursor.execute('''
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

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_logs (
                        id TEXT PRIMARY KEY,
                        template_id TEXT,
                        template_name TEXT NOT NULL,
                        recipient_email_hash TEXT NOT NULL,
                        recipient_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent_by BIGINT NOT NULL
                    )
                ''')

                if self.mode == "sqlite":
                    conn.commit()

            logger.info("Email Assistant database setup complete")
        except Exception as e:
            logger.error(f"Email Assistant database setup failed: {str(e)}")
            raise

    # ---------- Template Methods ---------- #

    def create_template(self, template_id: str, category: str, name: str,
                        subject: str, body: str, tone: str = 'formal',
                        placeholders: str = '[]') -> bool:
        query = '''
            INSERT INTO email_templates
            (id, category, name, subject, body, tone, placeholders)
            VALUES ({}, {}, {}, {}, {}, {}, {})
        '''.format(*(["%s"]*7 if self.mode == "postgres" else ["?"]*7))

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (template_id, category, name, subject, body, tone, placeholders))
                if self.mode == "sqlite":
                    conn.commit()
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Template already exists: {category}/{name}")
            return False
        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            return False

    def get_template(self, template_id: str):
        query = "SELECT * FROM email_templates WHERE id = %s" if self.mode == "postgres" else "SELECT * FROM email_templates WHERE id = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (template_id,))
            return cursor.fetchone()

    def get_template_by_name(self, category: str, name: str):
        query = "SELECT * FROM email_templates WHERE category = %s AND name = %s" if self.mode == "postgres" else "SELECT * FROM email_templates WHERE category = ? AND name = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (category, name))
            return cursor.fetchone()

    def get_templates_by_category(self, category: str):
        query = "SELECT * FROM email_templates WHERE category = %s ORDER BY name" if self.mode == "postgres" else "SELECT * FROM email_templates WHERE category = ? ORDER BY name"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (category,))
            return cursor.fetchall()

    def get_all_templates(self):
        query = "SELECT * FROM email_templates ORDER BY category, name"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        if not updates:
            return False
        keys = []
        values = []
        for k, v in updates.items():
            if k in ["category", "name", "subject", "body", "tone", "placeholders"]:
                keys.append(f"{k} = {'%s' if self.mode == 'postgres' else '?'}")
                values.append(v)
        if not keys:
            return False
        query = f"UPDATE email_templates SET {', '.join(keys)} WHERE id = {'%s' if self.mode == 'postgres' else '?'}"
        values.append(template_id)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(values))
                if self.mode == "sqlite":
                    conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update template: {str(e)}")
            return False

    def delete_template(self, template_id: str) -> bool:
        query = "DELETE FROM email_templates WHERE id = %s" if self.mode == "postgres" else "DELETE FROM email_templates WHERE id = ?"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (template_id,))
                if self.mode == "sqlite":
                    conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            return False

    # ---------- Logs Methods ---------- #

    def log_email(self, log_id: str, template_id: Optional[str], template_name: str,
                  recipient_email_hash: str, recipient_name: str, status: str,
                  sent_by: int, error_message: Optional[str] = None) -> bool:
        query = '''
            INSERT INTO email_logs
            (id, template_id, template_name, recipient_email_hash,
             recipient_name, status, error_message, sent_by)
            VALUES ({}, {}, {}, {}, {}, {}, {}, {})
        '''.format(*(["%s"]*8 if self.mode == "postgres" else ["?"]*8))

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    log_id, template_id, template_name, recipient_email_hash,
                    recipient_name, status, error_message, sent_by
                ))
                if self.mode == "sqlite":
                    conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to log email: {str(e)}")
            return False

    def get_email_logs(self, limit: int = 100, offset: int = 0,
                       status_filter: Optional[str] = None,
                       sent_by_filter: Optional[int] = None):
        query = "SELECT * FROM email_logs WHERE 1=1"
        params = []
        if status_filter:
            query += f" AND status = {'%s' if self.mode == 'postgres' else '?'}"
            params.append(status_filter)
        if sent_by_filter:
            query += f" AND sent_by = {'%s' if self.mode == 'postgres' else '?'}"
            params.append(sent_by_filter)
        query += " ORDER BY sent_at DESC LIMIT {} OFFSET {}".format(
            "%s" if self.mode == "postgres" else "?", "%s" if self.mode == "postgres" else "?"
        )
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def get_email_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM email_logs")
            total = cursor.fetchone()[0] if self.mode == "sqlite" else cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) FROM email_logs WHERE status = 'sent'")
            sent = cursor.fetchone()[0] if self.mode == "sqlite" else cursor.fetchone()["count"]

            cursor.execute('''
                SELECT template_name, COUNT(*) as usage_count
                FROM email_logs
                GROUP BY template_name
                ORDER BY usage_count DESC
                LIMIT {}
            '''.format("%s" if self.mode == "postgres" else "?"), (5,))
            popular = cursor.fetchall()

            cursor.execute('''
                SELECT COUNT(*) FROM email_logs
                WHERE sent_at >= (CURRENT_TIMESTAMP - INTERVAL '7 days')
            ''' if self.mode == "postgres" else '''
                SELECT COUNT(*) FROM email_logs
                WHERE sent_at >= datetime('now', '-7 days')
            ''')
            recent = cursor.fetchone()[0] if self.mode == "sqlite" else cursor.fetchone()["count"]

            return {
                "total_emails": total,
                "successful_emails": sent,
                "success_rate": (sent / total * 100) if total > 0 else 0,
                "popular_templates": [dict(row) for row in popular] if self.mode == "postgres" else [dict(row) for row in popular],
                "recent_activity": recent
            }

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        query = (
            f"DELETE FROM email_logs WHERE sent_at < (CURRENT_TIMESTAMP - INTERVAL '{days_to_keep} days')"
            if self.mode == "postgres" else
            "DELETE FROM email_logs WHERE sent_at < datetime('now', ?)"
        )
        params = () if self.mode == "postgres" else (f"-{days_to_keep} days",)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if self.mode == "sqlite":
                    conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")
            return 0


email_db = EmailDatabase()
