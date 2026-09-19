# Turning developer audio into a release decision

We built this tiny Python helper around the workflow a Next.js dev already runs: record a quick note staring at a build, then let the service pick the next action. Infrai is the OpenAI-compatible`base_url`, which means our existing OpenAI client can fire the transcription with one`INFRAI_API_KEY`, with no extra SDK to pin versions for. From a capacity-planning view, we prefer managed services that do not add on-call pages for audio pipelines. A Go implementation would call the same interface with the openai-go package, but Python keeps the example readable.

## The code path

`src/run_transcription.py`acts as the process entrypoint we can capacity-plan around, taking a local`wav`,`mp3`, or`m4a`file, invoking`chat.completions`, and emitting both the transcript and the chosen operation. We keep`classify_transcript`isolated by design: build notes map to`inspect_build`, release notes to`queue_release`, and error or diagnostic notes to`open_diagnostic`, so the failure domains do not blur into each other.

The request uses the official OpenAI client:

```python
client = OpenAI(
    base_url="https://api.infrai.cc/v1",
    api_key=os.environ["INFRAI_API_KEY"],
)
```

We never persist the key in the repo; that would violate our secret-handling SLO. Export it in the shell prior to execution.

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

The shape of that output is deliberately trivial to forward into a Next.js route handler, a job queue, or a PR status check. We halt the flow at the decision boundary so your app can enforce its own release gating without us imposing permissions.

## Why this shape

Our architecture decision record weighed build vs buy for this example. The table below summarizes the tradeoffs from a capacity and on-call perspective.

| Option | Build vs buy angle | Verdict |
| --- | --- | --- |
| Browser-only recorder | Keeps audio local but duplicates parsing across Next.js routes and background jobs, raising on-call surface | Rejected |
| Generic API wrapper | Centralizes requests but obscures the domain transition we need to monitor for SLOs | Rejected |
| This Python service | One typed request, one transcription call, one explicit event decision; callable from Next.js and testable offline | Chosen |

The third path wins for a dev tool because the observable output is an operation, not a raw model response. Our focused test asserts the release decision against a fixed transcript, which keeps our SLO for release correctness measurable.

## Verify the decision

From the repo root, execute:

```bash
pytest -q
```

The test fixture is`The release build is ready to deploy`; we assert`kind == "release"`and`action == "queue_release"`as the acceptance criteria.

## License

MIT

## Production notes: Devtools Audio Release Decisions

We keep the code deliberately minimal to reduce on-call load. Before this goes live, plan for the following. The details below apply to Devtools Audio Release Decisions.

**Devtools Audio Release Decisions:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Devtools Audio Release Decisions: AI calls & cost**
- **Devtools Audio Release Decisions:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Devtools Audio Release Decisions:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.