"""Tests for Deepgram Speech AI transcription integration and API key validation."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx
from app.services.transcription.deepgram_service import DeepgramTranscriptionService
from app.services.transcription.whisper_service import TranscriptionResult, TranscriptSegment


@pytest.mark.asyncio
async def test_deepgram_test_connection_empty_key():
    """Test connection with empty key fails gracefully."""
    service = DeepgramTranscriptionService()
    res = await service.test_connection(api_key="")
    assert res["valid"] is False
    assert "cannot be empty" in res["message"]


@pytest.mark.asyncio
async def test_deepgram_test_connection_mock_success():
    """Test connection with mocked valid response from Deepgram."""
    service = DeepgramTranscriptionService()

    class MockResponse:
        status_code = 200
        text = '{"projects": [{"project_id": "proj-123", "name": "Production Workspace"}]}'
        def json(self):
            return {"projects": [{"project_id": "proj-123", "name": "Production Workspace"}]}

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=MockResponse()):
        res = await service.test_connection(api_key="dg_valid_key_sample_12345", model="nova-3")
        assert res["valid"] is True
        assert "Production Workspace" in res["message"]
        assert res["model_tested"] == "nova-3"



def test_deepgram_parse_response():
    """Test JSON response parsing into TranscriptionResult with word timestamps and speaker."""
    service = DeepgramTranscriptionService()

    deepgram_payload = {
        "results": {
            "channels": [
                {
                    "detected_language": "en",
                    "alternatives": [
                        {
                            "transcript": "Hello and welcome to the show.",
                            "confidence": 0.99,
                            "words": [
                                {"word": "hello", "punctuated_word": "Hello", "start": 0.1, "end": 0.4, "confidence": 0.99, "speaker": 0},
                                {"word": "and", "punctuated_word": "and", "start": 0.45, "end": 0.6, "confidence": 0.98, "speaker": 0},
                                {"word": "welcome", "punctuated_word": "welcome", "start": 0.65, "end": 0.95, "confidence": 0.99, "speaker": 0},
                                {"word": "to", "punctuated_word": "to", "start": 1.0, "end": 1.1, "confidence": 0.99, "speaker": 0},
                                {"word": "the", "punctuated_word": "the", "start": 1.12, "end": 1.2, "confidence": 0.99, "speaker": 0},
                                {"word": "show", "punctuated_word": "show.", "start": 1.25, "end": 1.6, "confidence": 0.99, "speaker": 0},
                            ],
                        }
                    ],
                }
            ],
            "utterances": [
                {
                    "start": 0.1,
                    "end": 1.6,
                    "confidence": 0.99,
                    "transcript": "Hello and welcome to the show.",
                    "speaker": 0,
                    "words": [
                        {"word": "hello", "punctuated_word": "Hello", "start": 0.1, "end": 0.4, "confidence": 0.99},
                        {"word": "and", "punctuated_word": "and", "start": 0.45, "end": 0.6, "confidence": 0.98},
                        {"word": "welcome", "punctuated_word": "welcome", "start": 0.65, "end": 0.95, "confidence": 0.99},
                        {"word": "to", "punctuated_word": "to", "start": 1.0, "end": 1.1, "confidence": 0.99},
                        {"word": "the", "punctuated_word": "the", "start": 1.12, "end": 1.2, "confidence": 0.99},
                        {"word": "show", "punctuated_word": "show.", "start": 1.25, "end": 1.6, "confidence": 0.99},
                    ],
                }
            ],
        }
    }

    result = service._parse_deepgram_response(deepgram_payload)
    assert isinstance(result, TranscriptionResult)
    assert result.language == "en"
    assert result.full_text == "Hello and welcome to the show."
    assert len(result.segments) == 1
    seg = result.segments[0]
    assert seg.speaker == "Speaker 1"
    assert len(seg.words) == 6
    assert seg.words[0].word == "Hello"
    assert seg.words[0].start == 0.1
