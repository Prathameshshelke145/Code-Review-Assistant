# ADK Code Review Assistant

A local-first, multi-agent Python code review and code-fixing assistant built with **Google Agent Development Kit (ADK)** and the **Gemini Developer API (Google AI Studio)**.

This version is intended for local development on Windows, macOS, or Linux. It uses an AI Studio API key and does **not** require Google Cloud Application Default Credentials, Vertex AI, Cloud Run, Cloud SQL, or a Google Cloud Storage bucket.

> **Important:** Local execution does not mean offline execution. The agents still call the Gemini API over the internet, and model access is subject to the quota and billing limits of the Google AI Studio project associated with your API key.

## Features

### Code review pipeline

The root `CodeReviewAssistant` delegates Python code reviews to a sequential pipeline:

1. **Code Analyzer** – parses Python source and reports its structure (functions, classes, imports, and related observations).
2. **Style Checker** – checks Python style, including PEP 8 conventions, using `pycodestyle` and project-specific checks.
3. **Test Runner** – generates and runs tests for the submitted code and summarizes the results.
4. **Feedback Synthesizer** – combines the available analysis, style, and test results into review feedback.

### Code-fixing pipeline

When the user requests fixes, the root agent delegates to a second pipeline:

1. **Code Fixer** – proposes corrected code based on the review findings.
2. **Fix Test Runner** – tests the proposed fixed code.
3. **Fix Validator** – evaluates the fix results. The fix-attempt loop is configured for up to three iterations.
4. **Fix Synthesizer** – prepares the final fix summary/report.

The review and fix pipelines are defined in `code_review_assistant/agent.py`. Individual agents are in `code_review_assistant/sub_agents/`.

## Architecture

```text
User
  |
  v
ADK Web UI / ADK CLI
  |
  v
CodeReviewAssistant (root agent)
  |
  +------------------------------+
  |                              |
  v                              v
CodeReviewPipeline               CodeFixPipeline
(SequentialAgent)                (SequentialAgent)
  |                              |
  +--> CodeAnalyzer              +--> FixAttemptLoop (up to 3 iterations)
  |                              |      +--> CodeFixer
  +--> StyleChecker              |      +--> FixTestRunner
  |                              |      +--> FixValidator
  +--> TestRunner                |
  |                              +--> FixSynthesizer
  +--> FeedbackSynthesizer
  |
  v
Final review / fix response
```

## Requirements

- Python **3.10–3.12** (Python 3.11 is a good choice for this setup).
- A Google AI Studio API key.
- Internet access to call the Gemini API.
- Windows PowerShell, macOS Terminal, or Linux shell.

## 1. Get a Gemini API key

1. Open [Google AI Studio – API keys](https://aistudio.google.com/apikey).
2. Create or select an API key and its associated project.
3. Keep the key private. Do not commit it to Git or share it in screenshots/logs.
4. Check the project's available model quota at [Google AI Studio rate limits](https://ai.dev/rate-limit).

A `429 RESOURCE_EXHAUSTED` response means the selected model/project has reached a quota or has no quota available for that tier. In particular, a reported quota **limit of `0`** is not fixed by retrying or waiting: select a model with available quota for your project, or enable the appropriate billing/tier. See [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

## 2. Clone or extract the project

If you have the ZIP archive, extract it and open a terminal in the project root — the directory containing `requirements.txt`, `pyproject.toml`, and `code_review_assistant/`.

Alternatively:

```bash
git clone <your-repository-url>
cd <repository-folder>
```

Do not run the ADK commands from inside `code_review_assistant/`; run them from the project root so ADK can discover the agent package.

## 3. Create and activate a virtual environment

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, allow it for the current terminal only and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 4. Install dependencies

From the project root, with the virtual environment active:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify that ADK is installed:

```bash
adk --version
```

## 5. Configure environment variables

Copy the example environment file:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

Edit `.env` and set your real API key. For example:

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_API_KEY=replace_with_your_google_ai_studio_api_key

# Use model IDs that are available to your AI Studio project.
WORKER_MODEL=gemini-2.5-flash
CRITIC_MODEL=gemini-2.5-flash

PASSING_SCORE_THRESHOLD=0.8
STYLE_WEIGHT=0.3
TEST_WEIGHT=0.5
STRUCTURE_WEIGHT=0.2
MAX_GRADING_ATTEMPTS=3

LOG_LEVEL=INFO
DEBUG_MODE=false
```

**Model configuration notes:**

- `WORKER_MODEL` is used by the code-analysis, style, test, and fix agents, as well as the root agent.
- `CRITIC_MODEL` is used by the feedback and fix synthesizer agents.
- The values above are examples, not a guarantee of free-tier access. Check the model IDs and quota available to your own AI Studio project.
- If you encounter a 429 error for the Pro/critic model and its free-tier quota is `0`, temporarily set `CRITIC_MODEL` to a Flash model that has quota for your project. Setting both variables to the same available Flash model is a sensible baseline for local testing.
- The grading weights must add up to `1.0`; otherwise configuration validation fails.
- `GOOGLE_GENAI_USE_VERTEXAI=false` selects the Gemini Developer API rather than Vertex AI.

Do not put quotes around the API key unless they are part of the key. Do not commit `.env` to source control.

## 6. Run the assistant

### Option A: ADK Web UI (recommended)

From the project root, with the virtual environment active:

```bash
adk web --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser and select `code_review_assistant` if the UI asks you to choose an app/agent.

Keep the terminal running while using the UI. To stop the server, press `Ctrl+C` in that terminal.

### Option B: ADK CLI

From the same project root:

```bash
adk run code_review_assistant
```

This runs the agent in the terminal rather than the browser UI.

## 7. Try a code review

Paste a small Python example into the ADK interface:

```python
def calculate_total(price, quantity):
    total=price*quantity
    print(total)
    return total
```

Ask the assistant to review it. The review pipeline should analyze the code, check style, run its test workflow, and synthesize feedback. If the review identifies issues, ask the assistant to fix them and inspect the fix pipeline's output.

For a first test, use a small, non-sensitive Python snippet. Do not submit passwords, API keys, personal data, or proprietary source code unless you are authorized to send that content to the external Gemini API.

## 8. Run tests

The project includes a pytest integration-test entry point:

```bash
pytest -q
```

The integration tests use the ADK evaluation framework and require valid Gemini API access, available model quota, and the evaluation dataset files referenced by `tests/test_code_review_agent.py`. Check that those dataset files are present before expecting the integration tests to run successfully. The test suite is not an offline-only test suite.

A successful Python import check can be run from the project root:

```bash
python -c "from code_review_assistant.agent import root_agent; print(root_agent.name)"
```

## Configuration reference

| Variable | Purpose | Default in application |
|---|---|---|
| `GOOGLE_API_KEY` | Google AI Studio API key | Required for Gemini API calls |
| `GOOGLE_GENAI_USE_VERTEXAI` | Select Vertex AI vs Gemini Developer API | Forced to `false` by local config |
| `WORKER_MODEL` | Main worker model for root, analysis, style, testing, and fixing agents | `gemini-2.5-flash` |
| `CRITIC_MODEL` | Model for feedback and fix synthesis agents | `gemini-2.5-pro` |
| `PASSING_SCORE_THRESHOLD` | Configured grading threshold | `0.8` |
| `STYLE_WEIGHT` | Style component weight | `0.3` |
| `TEST_WEIGHT` | Test component weight | `0.5` |
| `STRUCTURE_WEIGHT` | Structure component weight | `0.2` |
| `MAX_GRADING_ATTEMPTS` | Configured maximum grading attempts | `3` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `DEBUG_MODE` | Debug-mode setting | `false` |

## Project structure

```text
.
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
├── code_review_assistant/
│   ├── __init__.py
│   ├── agent.py                  # Root agent and review/fix orchestration
│   ├── config.py                 # Local Gemini API configuration
│   ├── constants.py              # Shared ADK state keys
│   ├── tools.py                  # Analysis, style, grading and report tools
│   └── sub_agents/
│       ├── review_pipeline/
│       │   ├── code_analyzer.py
│       │   ├── style_checker.py
│       │   ├── test_runner.py
│       │   └── feedback_synthesizer.py
│       └── fix_pipeline/
│           ├── code_fixer.py
│           ├── fix_test_runner.py
│           ├── fix_validator.py
│           └── fix_synthesizer.py
└── tests/
    ├── test_code_review_agent.py
    └── integration/
        └── test_config.json
```

## Local data and runtime files

ADK Web creates local session storage and artifact data under `.adk/` directories. These files are runtime data, not source code. Do not delete them while the server is running if you need to retain the associated local session/artifact data. The exact storage location can depend on the ADK version and how the app is launched.

## Troubleshooting

### `429 RESOURCE_EXHAUSTED`

The selected model's quota is exhausted or unavailable for the current project/tier. Check [AI Studio rate limits](https://ai.dev/rate-limit). If a model reports a quota limit of `0`, switch to a model with an available quota or configure billing/eligible access. Retries cannot create quota that the project does not have.

### `401` or `403`

Check that `GOOGLE_API_KEY` is correct, active, and loaded from the project-root `.env` file. Confirm that the key belongs to the AI Studio project whose model quota you checked. Never paste the key into an issue or public log.

### Model not found / `404 NOT_FOUND`

Confirm the exact model ID currently supported for your API key and project. Update `WORKER_MODEL` and/or `CRITIC_MODEL` in `.env` accordingly. Model availability can change over time.

### `adk` is not recognized

Activate the virtual environment and reinstall dependencies:

```bash
python -m pip install -r requirements.txt
```

Then check `adk --version`.

### Agent or package not found

Run `adk web` or `adk run` from the project root — the directory containing the `code_review_assistant/` package.

### Port 8000 is already in use

Use another port, for example:

```bash
adk web --host 127.0.0.1 --port 8001
```

Then open `http://127.0.0.1:8001`.

### Request appears to hang

Check the terminal for the last Gemini request and any API error. A request may be waiting on the model API or quota. Test the same model and API key independently before changing agent orchestration. Keep the ADK server terminal open while a request is running.

## Security and usage notes

- Treat submitted code as potentially sensitive. Review your organization's policies before sending code to an external model provider.
- Never commit `.env`, API keys, credentials, or generated sensitive artifacts.
- Run only code you trust. Test execution can execute submitted/generated Python code; do not use this tool to run untrusted code on a machine containing valuable credentials or files.
- This project is a development assistant, not a security sandbox or a substitute for human code review.
- Review generated fixes before applying them to production code.

## Local version scope

This local setup is configured for the Gemini Developer API and ADK's local development interface/CLI. It does not include the original GCP deployment components such as Cloud Run deployment scripts, Vertex AI Agent Engine integration, or GCP service initialization. Those deployment paths must be configured separately if you later decide to deploy to Google Cloud.

## Useful links

- [Google ADK documentation](https://google.github.io/adk-docs/)
- [ADK – Gemini models](https://google.github.io/adk-docs/agents/models/google-gemini/)
- [Google AI Studio – API keys](https://aistudio.google.com/apikey)
- [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [AI Studio rate-limit dashboard](https://ai.dev/rate-limit)

## License

See [LICENSE](LICENSE) for the project's license.
