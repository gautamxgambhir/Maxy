import sqlite3
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.setup_database()

    def setup_database(self):
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS profiles (
                        discord_id TEXT PRIMARY KEY,
                        discord_username TEXT NOT NULL,
                        name TEXT NOT NULL,
                        skills TEXT,
                        interests TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_profile_timestamp
                    AFTER UPDATE ON profiles
                    BEGIN
                        UPDATE profiles SET updated_at = CURRENT_TIMESTAMP
                        WHERE discord_id = old.discord_id;
                    END;
                ''')
            logger.info("Database setup complete")
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()

    def upsert_profile(self, discord_id, discord_username, name, skills, interests):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO profiles (
                    discord_id, discord_username, name, skills, interests
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET
                    discord_username = excluded.discord_username,
                    name = excluded.name,
                    skills = excluded.skills,
                    interests = excluded.interests
            ''', (discord_id, discord_username, name, skills, interests))
            return cursor.lastrowid

    def search_profiles(self, skills=None, interests=None, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM profiles WHERE "
            conditions = []
            params = []
            
            if skills:
                skills_list = [f"%{skill.strip()}%" for skill in skills.split(",")]
                conditions.append(" OR ".join(["skills LIKE ?" for _ in skills_list]))
                params.extend(skills_list)
            
            if interests:
                interests_list = [f"%{interest.strip()}%" for interest in interests.split(",")]
                conditions.append(" OR ".join(["interests LIKE ?" for _ in interests_list]))
                params.extend(interests_list)
            
            if not conditions:
                return []
            
            query += " AND ".join([f"({c})" for c in conditions])
            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()

db = Database()