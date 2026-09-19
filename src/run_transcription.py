"""Command-line entry point for a developer-tools recording."""

import argparse

from devtools_transcription import TranscriptionRequest, handle_recording


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe a developer-tools audio clip")
    parser.add_argument("audio_path")
    parser.add_argument("--format", choices=["wav", "mp3", "m4a"], default="wav")
    args = parser.parse_args()
    event = handle_recording(TranscriptionRequest(args.audio_path, args.format))
    print(f"{event.kind}: {event.action}")
    print(event.text)


if __name__ == "__main__":
    main()
