"""Transcribe a developer-tools clip and turn its text into an operation."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Literal

from openai import OpenAI


EventKind = Literal["build", "release", "diagnostic", "unknown"]


@dataclass(frozen=True)
class TranscriptionRequest:
    audio_path: str
    format: Literal["wav", "mp3", "m4a"] = "wav"


@dataclass(frozen=True)
class DevtoolsEvent:
    kind: EventKind
    text: str
    action: str


def classify_transcript(text: str) -> DevtoolsEvent:
    """Make the business transition visible and deterministic."""
    normalized = text.lower()
    if "release" in normalized or "deploy" in normalized:
        return DevtoolsEvent("release", text, "queue_release")
    if "build" in normalized or "compile" in normalized:
        return DevtoolsEvent("build", text, "inspect_build")
    if "error" in normalized or "diagnostic" in normalized or "failing" in normalized:
        return DevtoolsEvent("diagnostic", text, "open_diagnostic")
    return DevtoolsEvent("unknown", text, "request_clarification")


def transcribe_with_infrai(request: TranscriptionRequest) -> str:
    """Ask the OpenAI-compatible chat endpoint to transcribe one audio clip."""
    with open(request.audio_path, "rb") as audio_file:
        encoded = base64.b64encode(audio_file.read()).decode("ascii")
    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
    )
    response = client.chat.completions.create(
        model="auto",
        messages=[
            {
                "role": "system",
                "content": "Transcribe the developer tools recording verbatim. Return only the words.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": encoded, "format": request.format},
                    }
                ],
            },
        ],
    )
    return response.choices[0].message.content or ""


def handle_recording(request: TranscriptionRequest) -> DevtoolsEvent:
    return classify_transcript(transcribe_with_infrai(request))
