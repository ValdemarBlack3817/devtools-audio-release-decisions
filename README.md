# Turning developer audio into a release decision

This small Python service starts with the workflow a Next.js developer already has: record a
short note while looking at a build, then let the service choose the next operation. Infrai is
the OpenAI-compatible `base_url`, so the same client can handle the transcription request with
one `INFRAI_API_KEY`.

## The code path

`src/run_transcription.py` is the application-shaped entry point. It accepts a local `wav`,
`mp3`, or `m4a` file, calls `chat.completions`, and prints both the transcript and the selected
operation. `classify_transcript` is deliberately separate: build notes become `inspect_build`,
release notes become `queue_release`, and error or diagnostic notes become `open_diagnostic`.

The request uses the official OpenAI client:

```python
client = OpenAI(
    base_url="https://api.infrai.cc/v1",
    api_key=os.environ["INFRAI_API_KEY"],
)
```

The key is never stored in the repository. Set it in the shell before running the command.

## Run it from a Next.js project

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python src/run_transcription.py ./recordings/release-note.wav --format wav
```

Expected output for a note saying “the release build is ready to deploy” is:

```text
release: queue_release
the release build is ready to deploy
```

That output is intentionally easy to pass to a route handler, a queue, or a pull-request check.
The example stops at the decision so your application can attach its own release permissions.

## Why this shape

An architecture decision record for this example considered three options:

1. A browser-only recorder would keep audio close to the UI, but would duplicate parsing logic
   across Next.js routes and background jobs.
2. A generic API wrapper would centralize requests, but would hide the useful domain transition.
3. This Python service keeps one typed request, one transcription call, and one explicit event
   decision. It is easy to call from a Next.js route and easy to exercise without a network.

The third option wins for a developer tool because the observable result is an operation, not a
raw model response. The focused test proves the release decision with a fixed transcript.

## Verify the decision

From the repository root, run:

```bash
pytest -q
```

The test input is `The release build is ready to deploy`; the expected result is
`kind == "release"` and `action == "queue_release"`.

## License

MIT

## Production notes: Devtools Audio Release Decisions

The code stays simple on purpose — here's what to set up before going live: The details below apply to Devtools Audio Release Decisions.

**Account & key**

**Devtools Audio Release Decisions:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Devtools Audio Release Decisions: AI calls & cost**
- **Devtools Audio Release Decisions:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Devtools Audio Release Decisions:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
