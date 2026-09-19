from src.devtools_transcription import classify_transcript


def test_release_recording_queues_release_operation() -> None:
    event = classify_transcript("The release build is ready to deploy")
    assert event.kind == "release"
    assert event.action == "queue_release"
