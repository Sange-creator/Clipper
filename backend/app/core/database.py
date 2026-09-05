"""Database setup, async engine and session management with automatic SQLite migrations."""

from collections.abc import AsyncGenerator
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import settings
from app.core.models import Base

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables and apply automatic migrations for SQLite."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Automatic column additions for existing SQLite databases
        migrations = [
            ("projects", "mode", "VARCHAR(32) DEFAULT 'podcast'"),
            ("jobs", "mode", "VARCHAR(32) DEFAULT 'podcast'"),
            ("jobs", "burn_captions", "BOOLEAN DEFAULT 1"),
            ("jobs", "remove_dead_air", "BOOLEAN DEFAULT 1"),
            ("jobs", "framing_mode", "VARCHAR(32) DEFAULT 'crop_9_16'"),
            ("jobs", "blur_radius", "INTEGER DEFAULT 30"),
            ("jobs", "subtitle_position", "INTEGER DEFAULT 75"),
            ("jobs", "add_hook_header", "BOOLEAN DEFAULT 0"),
            ("jobs", "hook_header_position", "INTEGER DEFAULT 12"),
            ("jobs", "hook_header_style", "VARCHAR(64) DEFAULT 'viral_creator'"),
            ("jobs", "remove_watermark", "BOOLEAN DEFAULT 0"),
            ("jobs", "watermark_position", "VARCHAR(32) DEFAULT 'top_right'"),
            ("jobs", "enhance_quality", "BOOLEAN DEFAULT 1"),
            ("jobs", "hook_strategy", "VARCHAR(32) DEFAULT 'teaser_climax_hook'"),
            ("clip_candidates", "standalone_score", "FLOAT DEFAULT 0.0"),
            ("clip_candidates", "rewatch_score", "FLOAT DEFAULT 0.0"),
            ("clip_candidates", "timeline_edit_json", "TEXT"),
            ("rendered_clips", "mode", "VARCHAR(32) DEFAULT 'podcast'"),
            ("rendered_clips", "burn_captions", "BOOLEAN DEFAULT 1"),
            ("rendered_clips", "framing_mode", "VARCHAR(32) DEFAULT 'crop_9_16'"),
            ("rendered_clips", "blur_radius", "INTEGER DEFAULT 30"),
            ("rendered_clips", "subtitle_position", "INTEGER DEFAULT 75"),
            ("rendered_clips", "add_hook_header", "BOOLEAN DEFAULT 0"),
            ("rendered_clips", "hook_header_position", "INTEGER DEFAULT 12"),
            ("rendered_clips", "hook_header_style", "VARCHAR(64) DEFAULT 'viral_creator'"),
            ("rendered_clips", "hook_header_text", "TEXT"),
            ("rendered_clips", "remove_watermark", "BOOLEAN DEFAULT 0"),
            ("rendered_clips", "watermark_position", "VARCHAR(32) DEFAULT 'top_right'"),
            ("rendered_clips", "enhance_quality", "BOOLEAN DEFAULT 1"),
            ("rendered_clips", "hook_strategy", "VARCHAR(32) DEFAULT 'teaser_climax_hook'"),
            ("rendered_clips", "timeline_edit_json", "TEXT"),
            ("rendered_clips", "single_para_copy", "TEXT"),
            ("rendered_clips", "part_index", "INTEGER"),
            ("rendered_clips", "total_parts", "INTEGER"),
            ("jobs", "genre", "VARCHAR(64) DEFAULT 'auto'"),
            ("jobs", "enable_series_parts", "BOOLEAN DEFAULT 1"),
        ]

        for table, col, col_type in migrations:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
            except Exception:
                # Column already exists
                pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a transactional async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
