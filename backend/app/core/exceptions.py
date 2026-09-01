"""Domain exceptions for the AI Video Clipper."""

from typing import Any, Optional


class ClipperException(Exception):
    """Base exception for all clipper operations."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class MediaValidationError(ClipperException):
    """Raised when an uploaded media file is invalid, corrupt, or unsupported."""
    pass


class MediaProcessingError(ClipperException):
    """Raised when an FFmpeg, OpenCV, or audio extraction operation fails."""
    pass


class TranscriptionError(ClipperException):
    """Raised when speech-to-text transcription fails."""
    pass


class AIProviderError(ClipperException):
    """Raised when an AI reasoning provider fails or returns unparseable content."""
    pass


class JobNotFoundError(ClipperException):
    """Raised when a requested processing job ID does not exist."""
    pass


class ClipNotFoundError(ClipperException):
    """Raised when a requested clip ID does not exist."""
    pass
