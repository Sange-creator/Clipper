"""Deepgram Speech-to-Text cloud transcription service with word-level timestamps and diarization."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import TranscriptionError
from app.services.transcription.whisper_service import (
    TranscriptSegment,
    TranscriptionResult,
    WordTimestamp,
)

logger = logging.getLogger(__name__)


class DeepgramTranscriptionService:
    """Production-grade Deepgram Nova-3 / Nova-2 STT integration."""

    DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"
    DEEPGRAM_PROJECTS_URL = "https://api.deepgram.com/v1/projects"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self.model = model or settings.DEEPGRAM_MODEL or "nova-3"

    async def test_connection(self, api_key: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Test Deepgram API Key validation and connectivity."""
        clean_key = api_key.strip()
        if not clean_key:
            return {"valid": False, "message": "Deepgram API key cannot be empty."}

        target_model = model or self.model or "nova-3"
        headers = {
            "Authorization": f"Token {clean_key}",
            "User-Agent": "AIClipper/3.0",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. Verify project/key authentication
                res = await client.get(self.DEEPGRAM_PROJECTS_URL, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    projects = data.get("projects", [])
                    proj_name = projects[0].get("name", "Default") if projects else "Active"
                    return {
                        "valid": True,
                        "message": f"Deepgram API connected successfully! (Project: {proj_name}, Model: {target_model})",
                        "model_tested": target_model,
                    }
                elif res.status_code == 401:
                    return {
                        "valid": False,
                        "message": "Invalid Deepgram API Key. Please check your credentials at console.deepgram.com.",
                        "model_tested": target_model,
                    }
                else:
                    return {
                        "valid": False,
                        "message": f"Deepgram verification returned status {res.status_code}: {res.text}",
                        "model_tested": target_model,
                    }
        except Exception as e:
            logger.error(f"Deepgram connection test failed: {e}")
            return {
                "valid": False,
                "message": f"Could not connect to Deepgram API: {str(e)}",
                "model_tested": target_model,
            }

    async def transcribe(
        self,
        audio_wav_path: Path | str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio file using Deepgram Speech AI with word-level timestamps,
        speaker diarization, smart formatting, and punctuation.
        """
        key = api_key or self.api_key or settings.DEEPGRAM_API_KEY
        if not key:
            raise TranscriptionError("Deepgram API Key is not configured.")

        audio_path = Path(audio_wav_path)
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_wav_path}")

        chosen_model = model or self.model or settings.DEEPGRAM_MODEL or "nova-3"

        params = {
            "model": chosen_model,
            "smart_format": "true",
            "punctuate": "true",
            "utterances": "true",
            "diarize": "true",
            "filler_words": "true",
        }

        headers = {
            "Authorization": f"Token {key.strip()}",
            "Content-Type": "audio/wav",
            "User-Agent": "AIClipper/3.0",
        }

        logger.info(f"Submitting audio to Deepgram ({chosen_model}): {audio_path.name}")

        try:
            # Read audio bytes
            audio_bytes = audio_path.read_bytes()

            async with httpx.AsyncClient(timeout=180.0) as client:
                res = await client.post(
                    self.DEEPGRAM_API_URL,
                    params=params,
                    headers=headers,
                    content=audio_bytes,
                )

                if res.status_code != 200:
                    error_msg = f"Deepgram API error ({res.status_code}): {res.text}"
                    logger.error(error_msg)
                    raise TranscriptionError(error_msg)

                data = res.json()
                return self._parse_deepgram_response(data)

        except httpx.RequestError as e:
            logger.error(f"Deepgram HTTP network request failed: {e}")
            raise TranscriptionError(f"Deepgram network error: {str(e)}")
        except Exception as e:
            logger.error(f"Deepgram transcription error: {e}")
            raise TranscriptionError(f"Deepgram transcription failed: {str(e)}")

    def _parse_deepgram_response(self, data: Dict[str, Any]) -> TranscriptionResult:
        """Parse Deepgram JSON payload into standardized TranscriptionResult."""
        results = data.get("results", {})
        channels = results.get("channels", [])
        if not channels:
            raise TranscriptionError("Deepgram returned empty channel results.")

        alt = channels[0].get("alternatives", [{}])[0]
        full_transcript = alt.get("transcript", "")
        detected_language = data.get("results", {}).get("channels", [{}])[0].get("detected_language") or "en"

        raw_words = alt.get("words", [])
        raw_utterances = results.get("utterances", [])

        segments: List[TranscriptSegment] = []

        if raw_utterances:
            for idx, utt in enumerate(raw_utterances):
                utt_words: List[WordTimestamp] = []
                for w in utt.get("words", []):
                    utt_words.append(
                        WordTimestamp(
                            word=w.get("punctuated_word", w.get("word", "")).strip(),
                            start=round(float(w.get("start", 0.0)), 2),
                            end=round(float(w.get("end", 0.0)), 2),
                            probability=round(float(w.get("confidence", 1.0)), 2),
                        )
                    )

                speaker_num = utt.get("speaker")
                speaker_str = f"Speaker {speaker_num + 1}" if speaker_num is not None else None

                segments.append(
                    TranscriptSegment(
                        id=idx,
                        start=round(float(utt.get("start", 0.0)), 2),
                        end=round(float(utt.get("end", 0.0)), 2),
                        text=utt.get("transcript", "").strip(),
                        words=utt_words,
                        confidence=round(float(utt.get("confidence", 1.0)), 2),
                        speaker=speaker_str,
                    )
                )
        elif raw_words:
            # Group words into sentence/time chunks if utterances not returned
            chunk_size = 12
            for idx, i in enumerate(range(0, len(raw_words), chunk_size)):
                slice_words = raw_words[i : i + chunk_size]
                chunk_start = slice_words[0].get("start", 0.0)
                chunk_end = slice_words[-1].get("end", chunk_start + 1.0)
                chunk_text = " ".join([w.get("punctuated_word", w.get("word", "")) for w in slice_words])

                word_timestamps = [
                    WordTimestamp(
                        word=w.get("punctuated_word", w.get("word", "")).strip(),
                        start=round(float(w.get("start", 0.0)), 2),
                        end=round(float(w.get("end", 0.0)), 2),
                        probability=round(float(w.get("confidence", 1.0)), 2),
                    )
                    for w in slice_words
                ]

                segments.append(
                    TranscriptSegment(
                        id=idx,
                        start=round(float(chunk_start), 2),
                        end=round(float(chunk_end), 2),
                        text=chunk_text.strip(),
                        words=word_timestamps,
                        confidence=0.95,
                    )
                )

        return TranscriptionResult(
            language=detected_language,
            full_text=full_transcript.strip(),
            segments=segments,
        )


deepgram_service = DeepgramTranscriptionService()
