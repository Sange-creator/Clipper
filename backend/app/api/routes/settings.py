"""System Settings and API Key management endpoints."""

import logging
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from google import genai
from groq import AsyncGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.models import SystemSetting
from app.core.schemas import (
    SettingsResponse,
    SettingsUpdateRequest,
    TestApiKeyRequest,
    TestApiKeyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])


def mask_key(key: Optional[str]) -> str:
    """Return masked API key string (e.g. AIzaSy...9x1z) for security."""
    if not key or len(key.strip()) == 0:
        return ""
    clean = key.strip()
    if len(clean) <= 8:
        return "****"
    return f"{clean[:6]}...{clean[-4:]}"


def sync_to_env_file() -> None:
    """Safely persist active runtime settings to backend/.env file so keys survive restarts and code changes."""
    env_path = settings.BASE_DIR / ".env"
    env_lines = [
        f"AI_PROVIDER={settings.AI_PROVIDER}",
        f"GEMINI_API_KEY={settings.GEMINI_API_KEY}",
        f"GEMINI_MODEL={settings.GEMINI_MODEL}",
        f"GROQ_API_KEY={settings.GROQ_API_KEY}",
        f"GROQ_MODEL={settings.GROQ_MODEL}",
        f"DEEPGRAM_API_KEY={settings.DEEPGRAM_API_KEY}",
        f"DEEPGRAM_MODEL={settings.DEEPGRAM_MODEL}",
        f"TRANSCRIBER_PROVIDER={settings.TRANSCRIBER_PROVIDER}",
        f"WHISPER_MODEL_SIZE={settings.WHISPER_MODEL_SIZE}",
    ]
    try:
        env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
        logger.info(f"Synchronized configuration to {env_path}")
    except Exception as e:
        logger.warning(f"Failed to write to .env file: {e}")


async def load_persisted_settings(db: AsyncSession) -> None:
    """Load settings stored in database into runtime settings and sync to .env."""
    stmt = select(SystemSetting)
    res = await db.execute(stmt)
    records = res.scalars().all()
    for rec in records:
        if rec.key == "AI_PROVIDER" and rec.value:
            settings.AI_PROVIDER = rec.value
        elif rec.key == "GEMINI_API_KEY" and rec.value:
            settings.GEMINI_API_KEY = rec.value
        elif rec.key == "GEMINI_MODEL" and rec.value:
            settings.GEMINI_MODEL = rec.value
        elif rec.key == "GROQ_API_KEY" and rec.value:
            settings.GROQ_API_KEY = rec.value
        elif rec.key == "GROQ_MODEL" and rec.value:
            settings.GROQ_MODEL = rec.value
        elif rec.key == "DEEPGRAM_API_KEY" and rec.value:
            settings.DEEPGRAM_API_KEY = rec.value
        elif rec.key == "DEEPGRAM_MODEL" and rec.value:
            settings.DEEPGRAM_MODEL = rec.value
        elif rec.key == "TRANSCRIBER_PROVIDER" and rec.value:
            settings.TRANSCRIBER_PROVIDER = rec.value
        elif rec.key == "WHISPER_MODEL_SIZE" and rec.value:
            settings.WHISPER_MODEL_SIZE = rec.value
        elif rec.key == "DEFAULT_FRAMING_MODE" and rec.value:
            settings.DEFAULT_FRAMING_MODE = rec.value
        elif rec.key == "DEFAULT_BLUR_RADIUS" and rec.value:
            try:
                settings.DEFAULT_BLUR_RADIUS = int(rec.value)
            except Exception:
                pass
        elif rec.key == "DEFAULT_SUBTITLE_POSITION" and rec.value:
            try:
                settings.DEFAULT_SUBTITLE_POSITION = int(rec.value)
            except Exception:
                pass
        elif rec.key == "DEFAULT_ADD_HOOK_HEADER" and rec.value:
            settings.DEFAULT_ADD_HOOK_HEADER = rec.value.lower() in ("true", "1", "yes")
        elif rec.key == "DEFAULT_HOOK_HEADER_POSITION" and rec.value:
            try:
                settings.DEFAULT_HOOK_HEADER_POSITION = int(rec.value)
            except Exception:
                pass
        elif rec.key == "DEFAULT_REMOVE_WATERMARK" and rec.value:
            settings.DEFAULT_REMOVE_WATERMARK = rec.value.lower() in ("true", "1", "yes")
        elif rec.key == "DEFAULT_WATERMARK_POSITION" and rec.value:
            settings.DEFAULT_WATERMARK_POSITION = rec.value
        elif rec.key == "DEFAULT_ENHANCE_QUALITY" and rec.value:
            settings.DEFAULT_ENHANCE_QUALITY = rec.value.lower() in ("true", "1", "yes")

    sync_to_env_file()


@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Retrieve current system configuration, active provider, and masked API keys."""
    await load_persisted_settings(db)

    ffmpeg_available = shutil.which("ffmpeg") is not None
    ffprobe_available = shutil.which("ffprobe") is not None

    return SettingsResponse(
        ai_provider=settings.AI_PROVIDER,
        gemini_api_key_configured=bool(settings.GEMINI_API_KEY),
        gemini_api_key_masked=mask_key(settings.GEMINI_API_KEY),
        gemini_model=settings.GEMINI_MODEL,
        groq_api_key_configured=bool(settings.GROQ_API_KEY),
        groq_api_key_masked=mask_key(settings.GROQ_API_KEY),
        groq_model=settings.GROQ_MODEL,
        deepgram_api_key_configured=bool(settings.DEEPGRAM_API_KEY),
        deepgram_api_key_masked=mask_key(settings.DEEPGRAM_API_KEY),
        deepgram_model=settings.DEEPGRAM_MODEL,
        transcriber_provider=settings.TRANSCRIBER_PROVIDER,
        whisper_model_size=settings.WHISPER_MODEL_SIZE,
        default_framing_mode=settings.DEFAULT_FRAMING_MODE,
        default_blur_radius=settings.DEFAULT_BLUR_RADIUS,
        default_subtitle_position=settings.DEFAULT_SUBTITLE_POSITION,
        default_add_hook_header=settings.DEFAULT_ADD_HOOK_HEADER,
        default_hook_header_position=settings.DEFAULT_HOOK_HEADER_POSITION,
        default_remove_watermark=settings.DEFAULT_REMOVE_WATERMARK,
        default_watermark_position=settings.DEFAULT_WATERMARK_POSITION,
        default_enhance_quality=settings.DEFAULT_ENHANCE_QUALITY,
        ffmpeg_available=ffmpeg_available,
        ffprobe_available=ffprobe_available,
    )


@router.post("", response_model=SettingsResponse)
async def update_settings(
    req: SettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update AI provider keys and models. Persists changes to SQLite database
    and updates active server runtime configuration immediately.
    """
    async def set_or_update(key: str, val: str):
        existing = await db.get(SystemSetting, key)
        if existing:
            existing.value = val
        else:
            db.add(SystemSetting(key=key, value=val))

    if req.ai_provider is not None:
        settings.AI_PROVIDER = req.ai_provider
        await set_or_update("AI_PROVIDER", req.ai_provider)

    if req.gemini_api_key is not None:
        clean_key = req.gemini_api_key.strip()
        settings.GEMINI_API_KEY = clean_key
        await set_or_update("GEMINI_API_KEY", clean_key)

    if req.gemini_model is not None:
        settings.GEMINI_MODEL = req.gemini_model.strip()
        await set_or_update("GEMINI_MODEL", req.gemini_model.strip())

    if req.groq_api_key is not None:
        clean_key = req.groq_api_key.strip()
        settings.GROQ_API_KEY = clean_key
        await set_or_update("GROQ_API_KEY", clean_key)

    if req.groq_model is not None:
        settings.GROQ_MODEL = req.groq_model.strip()
        await set_or_update("GROQ_MODEL", req.groq_model.strip())

    if req.deepgram_api_key is not None:
        clean_key = req.deepgram_api_key.strip()
        settings.DEEPGRAM_API_KEY = clean_key
        await set_or_update("DEEPGRAM_API_KEY", clean_key)

    if req.deepgram_model is not None:
        settings.DEEPGRAM_MODEL = req.deepgram_model.strip()
        await set_or_update("DEEPGRAM_MODEL", req.deepgram_model.strip())

    if req.transcriber_provider is not None:
        settings.TRANSCRIBER_PROVIDER = req.transcriber_provider.strip()
        await set_or_update("TRANSCRIBER_PROVIDER", req.transcriber_provider.strip())

    if req.whisper_model_size is not None:
        settings.WHISPER_MODEL_SIZE = req.whisper_model_size
        await set_or_update("WHISPER_MODEL_SIZE", req.whisper_model_size)

    if req.default_framing_mode is not None:
        settings.DEFAULT_FRAMING_MODE = req.default_framing_mode
        await set_or_update("DEFAULT_FRAMING_MODE", req.default_framing_mode)

    if req.default_blur_radius is not None:
        settings.DEFAULT_BLUR_RADIUS = req.default_blur_radius
        await set_or_update("DEFAULT_BLUR_RADIUS", str(req.default_blur_radius))

    if req.default_subtitle_position is not None:
        settings.DEFAULT_SUBTITLE_POSITION = req.default_subtitle_position
        await set_or_update("DEFAULT_SUBTITLE_POSITION", str(req.default_subtitle_position))

    if req.default_add_hook_header is not None:
        settings.DEFAULT_ADD_HOOK_HEADER = req.default_add_hook_header
        await set_or_update("DEFAULT_ADD_HOOK_HEADER", str(req.default_add_hook_header))

    if req.default_hook_header_position is not None:
        settings.DEFAULT_HOOK_HEADER_POSITION = req.default_hook_header_position
        await set_or_update("DEFAULT_HOOK_HEADER_POSITION", str(req.default_hook_header_position))

    if req.default_remove_watermark is not None:
        settings.DEFAULT_REMOVE_WATERMARK = req.default_remove_watermark
        await set_or_update("DEFAULT_REMOVE_WATERMARK", str(req.default_remove_watermark))

    if req.default_watermark_position is not None:
        settings.DEFAULT_WATERMARK_POSITION = req.default_watermark_position
        await set_or_update("DEFAULT_WATERMARK_POSITION", req.default_watermark_position)

    if req.default_enhance_quality is not None:
        settings.DEFAULT_ENHANCE_QUALITY = req.default_enhance_quality
        await set_or_update("DEFAULT_ENHANCE_QUALITY", str(req.default_enhance_quality))

    await db.commit()
    sync_to_env_file()
    logger.info(f"System settings updated: Provider={settings.AI_PROVIDER}, Framing={settings.DEFAULT_FRAMING_MODE}, SubtitlePos={settings.DEFAULT_SUBTITLE_POSITION}%, HookHeader={settings.DEFAULT_ADD_HOOK_HEADER}@{settings.DEFAULT_HOOK_HEADER_POSITION}%, Delogo={settings.DEFAULT_REMOVE_WATERMARK}@{settings.DEFAULT_WATERMARK_POSITION}, Enhance={settings.DEFAULT_ENHANCE_QUALITY}")

    return await get_settings(db)





@router.post("/test", response_model=TestApiKeyResponse)
async def test_api_key(req: TestApiKeyRequest):
    """
    Test live connectivity and validation of a pasted or configured API key.
    """
    key = req.api_key.strip() if req.api_key else ""
    if not key:
        if req.provider == "gemini" and settings.GEMINI_API_KEY:
            key = settings.GEMINI_API_KEY
        elif req.provider == "groq" and settings.GROQ_API_KEY:
            key = settings.GROQ_API_KEY
        elif req.provider == "deepgram" and settings.DEEPGRAM_API_KEY:
            key = settings.DEEPGRAM_API_KEY

    if not key:
        return TestApiKeyResponse(
            valid=False,
            message="API key cannot be empty. Please paste your API key.",
            model_tested=req.provider,
        )

    if req.provider == "deepgram":
        from app.services.transcription.deepgram_service import deepgram_service
        res = await deepgram_service.test_connection(key, req.model or settings.DEEPGRAM_MODEL)
        return TestApiKeyResponse(
            valid=res["valid"],
            message=res["message"],
            model_tested=res.get("model_tested", req.model or "nova-3"),
        )

    elif req.provider == "gemini":
        candidate_models = [
            req.model or settings.GEMINI_MODEL,
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        # Deduplicate while preserving order
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

        last_error = None
        for model_name in candidate_models:
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents="Respond with 'OK' if you can read this.",
                )
                if response.text:
                    settings.GEMINI_MODEL = model_name
                    return TestApiKeyResponse(
                        valid=True,
                        message=f"Gemini API key is valid and successfully connected to {model_name}!",
                        model_tested=model_name,
                    )
            except Exception as e:
                last_error = e
                continue

        logger.warning(f"Gemini API key test failed across models: {last_error}")
        return TestApiKeyResponse(
            valid=False,
            message=f"Gemini verification failed: {str(last_error)}",
            model_tested=candidate_models[0],
        )

    elif req.provider == "groq":
        try:
            client = AsyncGroq(api_key=key)
            # 1. Fetch available models from Groq account
            models_res = await client.models.list()
            available_ids = [m.id for m in models_res.data if not m.id.startswith("whisper") and "guard" not in m.id]

            # Priority candidates
            preferred = [
                req.model,
                settings.GROQ_MODEL,
                "qwen/qwen3.6-27b",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "groq/compound",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
            ]
            ordered_candidates = [m for m in preferred if m and m in available_ids]
            for m in available_ids:
                if m not in ordered_candidates:
                    ordered_candidates.append(m)

            if not ordered_candidates:
                ordered_candidates = available_ids or ["qwen/qwen3.6-27b"]

            last_error = None
            for model_name in ordered_candidates:
                try:
                    chat = await client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Respond with OK"}],
                        max_tokens=5,
                    )
                    if chat.choices and len(chat.choices) > 0:
                        settings.GROQ_MODEL = model_name
                        return TestApiKeyResponse(
                            valid=True,
                            message=f"Groq API key verified and connected successfully to {model_name}!",
                            model_tested=model_name,
                        )
                except Exception as e:
                    last_error = e
                    continue

            return TestApiKeyResponse(
                valid=False,
                message=f"Groq models available ({', '.join(available_ids[:3])}) failed: {str(last_error)}",
                model_tested=ordered_candidates[0],
            )
        except Exception as e:
            logger.warning(f"Groq API authentication failed: {e}")
            return TestApiKeyResponse(
                valid=False,
                message=f"Groq verification failed: {str(e)}",
                model_tested=req.model or "groq",
            )

    raise HTTPException(status_code=400, detail="Invalid provider requested.")

