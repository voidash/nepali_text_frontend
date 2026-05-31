"""Nepali text frontend for TTS.

Pipeline: raw Devanagari text → unicode normalize → tokenize →
text-normalize → akshara parse → base map → post-rules → phones + trace.
"""

__version__ = "0.1.0"

from .frontend import FrontendResult, TokenResult, process

__all__ = ["FrontendResult", "TokenResult", "process"]
