import os
import sqlite3
import psycopg2
import psycopg2.extras
import logging
import secrets
import threading
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.lock = threading.Lock()
        self.database_url = Config.DATABASE_URL
        if self.database_url:
            self.mode = "postgres"
        else:
            self.mode = "sqlite"
            self.db_path = Config.DATABASE_PATH
        self.setup_database()

    @contextmanager
    def get_connection(self):
        """Return a connection depending on mode (Postgres or SQLite)."""
        self.lock.acquire()
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
            conn.close()
            self.lock.release()

    def setup_database(self):
        """Create tables if they don’t exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) if self.mode == "postgres" else conn.cursor()

                # Profiles table
                cursor.execute('''
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

                # Teams table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teams (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        code TEXT UNIQUE NOT NULL,
                        owner_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Team members table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS team_members (
                        team_id INTEGER NOT NULL,
                        discord_id TEXT NOT NULL,
                        discord_username TEXT NOT NULL,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (team_id, discord_id)
                    )
                ''')

                if self.mode == "sqlite":
                    conn.commit()

            logger.info("Database setup complete")
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise

    # ---------------- PROFILE METHODS ---------------- #

    def upsert_profile(self, discord_id, discord_username, name, skills, interests):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.mode == "postgres":
                cursor.execute('''
                    INSERT INTO profiles (discord_id, discord_username, name, skills, interests)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (discord_id) DO UPDATE SET
                        discord_username = EXCLUDED.discord_username,
                        name = EXCLUDED.name,
                        skills = EXCLUDED.skills,
                        interests = EXCLUDED.interests
                ''', (discord_id, discord_username, name, skills, interests))
            else:
                cursor.execute('''
                    INSERT INTO profiles (discord_id, discord_username, name, skills, interests)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(discord_id) DO UPDATE SET
                        discord_username = excluded.discord_username,
                        name = excluded.name,
                        skills = excluded.skills,
                        interests = excluded.interests
                ''', (discord_id, discord_username, name, skills, interests))
                conn.commit()
            return True

    def get_profile(self, discord_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM profiles WHERE discord_id = %s" if self.mode == "postgres" else "SELECT * FROM profiles WHERE discord_id = ?"
            cursor.execute(query, (discord_id,))
            return cursor.fetchone()

    def search_profiles(self, skills=None, interests=None, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions, params = [], []

            if skills:
                skills_list = [f"%{skill.strip()}%" for skill in skills.split(",")]
                conditions.append(" OR ".join(["skills LIKE %s" if self.mode == "postgres" else "skills LIKE ?" for _ in skills_list]))
                params.extend(skills_list)

            if interests:
                interests_list = [f"%{interest.strip()}%" for interest in interests.split(",")]
                conditions.append(" OR ".join(["interests LIKE %s" if self.mode == "postgres" else "interests LIKE ?" for _ in interests_list]))
                params.extend(interests_list)

            if not conditions:
                return []

            query = "SELECT * FROM profiles WHERE " + " AND ".join([f"({c})" for c in conditions]) + " ORDER BY updated_at DESC LIMIT %s"
            if self.mode == "sqlite":
                query = query.replace("%s", "?")
            params.append(limit)

            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    # ---------------- TEAM METHODS ---------------- #

    def create_team(self, name, owner_id, owner_username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            code = secrets.token_hex(4).upper()
            try:
                if self.mode == "postgres":
                    cursor.execute(
                        "INSERT INTO teams (name, code, owner_id) VALUES (%s, %s, %s) RETURNING id",
                        (name, code, owner_id)
                    )
                    team_id = cursor.fetchone()["id"]
                    cursor.execute(
                        "INSERT INTO team_members (team_id, discord_id, discord_username) VALUES (%s, %s, %s)",
                        (team_id, owner_id, owner_username)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO teams (name, code, owner_id) VALUES (?, ?, ?)",
                        (name, code, owner_id)
                    )
                    team_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO team_members (team_id, discord_id, discord_username) VALUES (?, ?, ?)",
                        (team_id, owner_id, owner_username)
                    )
                    conn.commit()
                return team_id, code
            except Exception:
                return self.create_team(name, owner_id, owner_username)

    def add_team_member(self, team_id, discord_id, discord_username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "INSERT INTO team_members (team_id, discord_id, discord_username) VALUES (%s, %s, %s)" if self.mode == "postgres" else "INSERT INTO team_members (team_id, discord_id, discord_username) VALUES (?, ?, ?)"
            cursor.execute(query, (team_id, discord_id, discord_username))
            if self.mode == "sqlite":
                conn.commit()

    def remove_team_member(self, discord_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "DELETE FROM team_members WHERE discord_id = %s" if self.mode == "postgres" else "DELETE FROM team_members WHERE discord_id = ?"
            cursor.execute(query, (discord_id,))
            if self.mode == "sqlite":
                conn.commit()
            return cursor.rowcount > 0

    def get_team_by_code(self, code):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM teams WHERE code = %s" if self.mode == "postgres" else "SELECT * FROM teams WHERE code = ?"
            cursor.execute(query, (code,))
            return cursor.fetchone()

    def get_team_by_member(self, discord_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT t.*, tm.joined_at
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.discord_id = %s
            ''' if self.mode == "postgres" else '''
                SELECT t.*, tm.joined_at
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.discord_id = ?
            '''
            cursor.execute(query, (discord_id,))
            return cursor.fetchone()

    def get_team_members(self, team_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM team_members WHERE team_id = %s ORDER BY joined_at" if self.mode == "postgres" else "SELECT * FROM team_members WHERE team_id = ? ORDER BY joined_at"
            cursor.execute(query, (team_id,))
            return cursor.fetchall()

    def delete_team_if_empty(self, team_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM team_members WHERE team_id = %s" if self.mode == "postgres" else "SELECT COUNT(*) FROM team_members WHERE team_id = ?"
            cursor.execute(query, (team_id,))
            count = cursor.fetchone()[0] if self.mode == "sqlite" else cursor.fetchone()["count"]

            if count == 0:
                query = "DELETE FROM teams WHERE id = %s" if self.mode == "postgres" else "DELETE FROM teams WHERE id = ?"
                cursor.execute(query, (team_id,))
                if self.mode == "sqlite":
                    conn.commit()
                return True
            return False

    def delete_team(self, team_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            q1 = "DELETE FROM team_members WHERE team_id = %s" if self.mode == "postgres" else "DELETE FROM team_members WHERE team_id = ?"
            q2 = "DELETE FROM teams WHERE id = %s" if self.mode == "postgres" else "DELETE FROM teams WHERE id = ?"
            cursor.execute(q1, (team_id,))
            cursor.execute(q2, (team_id,))
            if self.mode == "sqlite":
                conn.commit()

    def transfer_team_ownership(self, team_id, new_owner_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "UPDATE teams SET owner_id = %s WHERE id = %s" if self.mode == "postgres" else "UPDATE teams SET owner_id = ? WHERE id = ?"
            cursor.execute(query, (new_owner_id, team_id))
            if self.mode == "sqlite":
                conn.commit()


db = Database()
