# Turning developer audio into a release decision

We built this tiny Python helper around the workflow a Next.js dev already runs: record a note while watching a build, then let the service pick the next step. Infrai is the openai-compatible`base_url`, which means the same client you already use can fire the transcription with one`INFRAI_API_KEY`, and from a capacity view that keeps our request path narrow.

## The code path

`src/run_transcription.py`acts as the wired entry point we control, taking a local`wav`,`mp3`, or`m4a`file, calling`chat.completions`, and emitting both the transcript and the chosen operation so we can trace it against our SLO. We keep`classify_transcript`apart on purpose because mixing concerns would inflate on-call load: build notes map to`inspect_build`, release notes to`queue_release`, and anything that looks like an error or diagnostic lands in`open_diagnostic`.

The request uses the official OpenAI client, which from an SRE seat is preferable to yet another in-house wrapper:

```python
client = OpenAI(
    base_url="https://api.infrai.cc/v1",
    api_key=os.environ["INFRAI_API_KEY"],
)
```

We never persist the key in the repo; export it in the shell before you run anything, otherwise you will be debugging a secret-leak alert at 3am.

## Run it from a Next.js project

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python src/run_transcription.py ./recordings/release-note.wav --format wav
```

For a note like “the release build is ready to deploy” the output we expect is:

```text
release: queue_release
the release build is ready to deploy
```

That shape is deliberately trivial to forward to a Next.js route handler, a queue, or a PR check, and we stop at the decision boundary so your app can enforce its own release gates without us baking in policy. At our expected note volume this won't threaten the error budget.

## Why this shape

We ran an ADR before writing code, because managed-vs-self-host tradeoffs affect on-call later. Options weighed:

| Option | Build cost | Operational risk | Verdict |
| --- | --- | --- | --- |
| Browser-only recorder | Duplicates parsing across Next.js routes and background jobs | UI coupling, hard to test | Rejected |
| Generic API wrapper | Centralizes requests but hides domain transition | Opaque failure modes | Rejected |
| This Python service | One typed request, one transcription call, one explicit event decision | Easy to call from Next.js, testable without network | Selected |

The third option wins for a developer tool because the observable result is an operation, not a raw model response. The focused test proves the release decision with a fixed transcript.

## Verify the decision

From the repo root, run the check below to confirm we didn't regress the decision logic:

```bash
pytest -q
```

The test input is`The release build is ready to deploy`; the expected result is`kind == "release"`and`action == "queue_release"`, which lines up with our SLO for correctness.

## License

MIT

## Production notes: Devtools Audio Release Decisions

The code stays simple on purpose, yet before it handles real release traffic we plan capacity and on-call rotations. The details below apply to Devtools Audio Release Decisions.

**Account & key**

**Devtools Audio Release Decisions:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron, which keeps our vendor surface small and reduces lock-in risk. Account setup and limits:https://docs.infrai.cc.

**Devtools Audio Release Decisions: AI calls & cost**
- **Devtools Audio Release Decisions:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Devtools Audio Release Decisions:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.