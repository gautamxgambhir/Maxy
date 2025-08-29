import sqlite3
import logging
import secrets
from contextlib import contextmanager
from config import Config
import threading

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.lock = threading.Lock()
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
                    CREATE TABLE IF NOT EXISTS teams (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        code TEXT UNIQUE NOT NULL,
                        owner_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(owner_id) REFERENCES profiles(discord_id)
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS team_members (
                        team_id INTEGER NOT NULL,
                        discord_id TEXT NOT NULL,
                        discord_username TEXT NOT NULL,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
                        FOREIGN KEY(discord_id) REFERENCES profiles(discord_id),
                        PRIMARY KEY (team_id, discord_id)
                    )
                ''')

                conn.execute('CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_members_discord ON team_members(discord_id)')

                conn.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_profile_timestamp
                    AFTER UPDATE ON profiles
                    BEGIN
                        UPDATE profiles SET updated_at = CURRENT_TIMESTAMP
                        WHERE discord_id = old.discord_id;
                    END
                ''')

            logger.info("Database setup complete")
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
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
                logger.error(f"Database error: {str(e)}")
                raise
            finally:
                conn.close()
        finally:
            self.lock.release()

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

    def get_profile(self, discord_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM profiles WHERE discord_id = ?
            ''', (discord_id,))
            return cursor.fetchone()

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

    def create_team(self, name, owner_id, owner_username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            code = secrets.token_hex(4).upper()
            try:
                cursor.execute(
                    "INSERT INTO teams (name, code, owner_id) VALUES (?, ?, ?)",
                    (name, code, owner_id)
                )
                team_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO team_members (team_id, discord_id, discord_username) VALUES (?, ?, ?)",
                    (team_id, owner_id, owner_username)
                )
                return team_id, code
            except sqlite3.IntegrityError:
                return self.create_team(name, owner_id, owner_username)

    def add_team_member(self, team_id, discord_id, discord_username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO team_members (team_id, discord_id, discord_username) VALUES (?, ?, ?)",
                (team_id, discord_id, discord_username)
            )

    def remove_team_member(self, discord_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM team_members WHERE discord_id = ?",
                (discord_id,)
            )
            return cursor.rowcount > 0

    def get_team_by_code(self, code):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM teams WHERE code = ?",
                (code,)
            )
            return cursor.fetchone()

    def get_team_by_member(self, discord_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, tm.joined_at
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.discord_id = ?
            ''', (discord_id,))
            return cursor.fetchone()

    def get_team_members(self, team_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM team_members WHERE team_id = ? ORDER BY joined_at",
                (team_id,)
            )
            return cursor.fetchall()

    def delete_team_if_empty(self, team_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM team_members WHERE team_id = ?",
                (team_id,)
            )
            count = cursor.fetchone()[0]

            if count == 0:
                cursor.execute(
                    "DELETE FROM teams WHERE id = ?",
                    (team_id,)
                )
                return True
            return False

    def delete_team(self, team_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM team_members WHERE team_id = ?",
                (team_id,)
            )
            cursor.execute(
                "DELETE FROM teams WHERE id = ?",
                (team_id,)
            )

    def transfer_team_ownership(self, team_id, new_owner_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE teams SET owner_id = ? WHERE id = ?",
                (new_owner_id, team_id)
            )

db = Database()