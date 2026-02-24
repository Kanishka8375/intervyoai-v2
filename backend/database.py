"""
SQLite Database Module for IntervyoAI
Stores conversations, settings, and history locally
"""

import os
import json
import asyncio
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

DATABASE_PATH = os.path.expanduser("~/.intervyoai/data.db")


@dataclass
class Conversation:
    id: Optional[int] = None
    role: str = ""
    content: str = ""
    timestamp: str = ""
    role_id: Optional[str] = None
    provider: Optional[str] = None


@dataclass
class Settings:
    id: int = 1
    job_role: str = "software_engineer"
    language: str = "en"
    model_name: str = "llama3.1:latest"
    temperature: float = 0.7
    auto_start: bool = False
    stealth_mode: bool = False
    overlay_opacity: float = 0.85


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    async def init(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role_id TEXT,
                    provider TEXT
                )
            """)

            # Settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    job_role TEXT DEFAULT 'software_engineer',
                    language TEXT DEFAULT 'en',
                    model_name TEXT DEFAULT 'llama3.1:latest',
                    temperature REAL DEFAULT 0.7,
                    auto_start INTEGER DEFAULT 0,
                    stealth_mode INTEGER DEFAULT 0,
                    overlay_opacity REAL DEFAULT 0.85
                )
            """)

            # Screenshots table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_data TEXT,
                    timestamp TEXT NOT NULL,
                    region TEXT,
                    analysis TEXT
                )
            """)

            # Initialize default settings if not exists
            await db.execute("""
                INSERT OR IGNORE INTO settings (id) VALUES (1)
            """)

            await db.commit()

    async def add_conversation(
        self, role: str, content: str, role_id: str = None, provider: str = None
    ) -> int:
        """Add a conversation message"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO conversations (role, content, timestamp, role_id, provider)
                   VALUES (?, ?, ?, ?, ?)""",
                (role, content, datetime.now().isoformat(), role_id, provider),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_conversations(
        self, limit: int = 50, role_id: str = None
    ) -> List[Conversation]:
        """Get conversation history"""
        async with aiosqlite.connect(self.db_path) as db:
            if role_id:
                rows = await db.execute(
                    """SELECT id, role, content, timestamp, role_id, provider
                       FROM conversations WHERE role_id = ? ORDER BY id DESC LIMIT ?""",
                    (role_id, limit),
                )
            else:
                rows = await db.execute(
                    """SELECT id, role, content, timestamp, role_id, provider
                       FROM conversations ORDER BY id DESC LIMIT ?""",
                    (limit,),
                )

            results = []
            async for row in rows:
                results.append(
                    Conversation(
                        id=row[0],
                        role=row[1],
                        content=row[2],
                        timestamp=row[3],
                        role_id=row[4],
                        provider=row[5],
                    )
                )
            return list(reversed(results))

    async def clear_conversations(self):
        """Clear conversation history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM conversations")
            await db.commit()

    async def get_settings(self) -> Settings:
        """Get application settings"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM settings WHERE id = 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return Settings(
                        id=row["id"],
                        job_role=row["job_role"],
                        language=row["language"],
                        model_name=row["model_name"],
                        temperature=row["temperature"],
                        auto_start=bool(row["auto_start"]),
                        stealth_mode=bool(row["stealth_mode"]),
                        overlay_opacity=row["overlay_opacity"],
                    )
                return Settings()

    async def update_settings(self, settings: Settings):
        """Update application settings"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE settings SET
                   job_role = ?,
                   language = ?,
                   model_name = ?,
                   temperature = ?,
                   auto_start = ?,
                   stealth_mode = ?,
                   overlay_opacity = ?
                   WHERE id = 1""",
                (
                    settings.job_role,
                    settings.language,
                    settings.model_name,
                    settings.temperature,
                    int(settings.auto_start),
                    int(settings.stealth_mode),
                    settings.overlay_opacity,
                ),
            )
            await db.commit()

    async def save_screenshot(
        self, image_data: str, region: str = None, analysis: str = None
    ) -> int:
        """Save screenshot to database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO screenshots (image_data, timestamp, region, analysis)
                   VALUES (?, ?, ?, ?)""",
                (image_data, datetime.now().isoformat(), region, analysis),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_screenshots(self, limit: int = 10) -> List[Dict]:
        """Get saved screenshots"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM screenshots ORDER BY id DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def search_conversations(self, query: str) -> List[Conversation]:
        """Search conversations"""
        async with aiosqlite.connect(self.db_path) as db:
            rows = await db.execute(
                """SELECT id, role, content, timestamp, role_id, provider
                   FROM conversations
                   WHERE content LIKE ? ORDER BY id DESC LIMIT 50""",
                (f"%{query}%",),
            )

            results = []
            async for row in rows:
                results.append(
                    Conversation(
                        id=row[0],
                        role=row[1],
                        content=row[2],
                        timestamp=row[3],
                        role_id=row[4],
                        provider=row[5],
                    )
                )
            return list(reversed(results))


# Global database instance
db = Database()


async def init_database():
    """Initialize the database"""
    await db.init()
