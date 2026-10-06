# Medical device field-service voice agent (multi-agent)

A voice-first medical device field-service agent built on the OpenAI Agents SDK Realtime API. A supervisor routes spoken requests to specialists that look up devices, check service cases, and pull troubleshooting guides. All catalog data lives in [`demo_catalog.py`](demo_catalog.py) — synthetic fixtures only, with no external API calls beyond the LLM.

Each specialist has access to only its own tool:

| Agent | Tool |
|-------|------|
| Device Registry Agent | `lookup_device` |
| Case Status Agent | `get_service_case` |
| Troubleshooting Agent | `get_troubleshooting_guide` |

Agent definitions and handoffs live in [`voice_agents.py`](voice_agents.py). Tools and catalog wiring live in [`demo_tools.py`](demo_tools.py) and [`demo_catalog.py`](demo_catalog.py).

## Setup

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3, and a working microphone and speaker.

1. Create a virtual environment, activate it, and install dependencies (from the repo root):

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

   On macOS, if `sounddevice` fails to load, install PortAudio first: `brew install portaudio`.

2. Copy the example env file and fill in your values:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at least `OPENAI_API_KEY` (required for the voice agent). For Arize tracing, set `ARIZE_API_KEY`, `ARIZE_SPACE_ID`, and optionally `ARIZE_PROJECT_NAME` (default in the example: `stryker-voice-service-demo`).

3. Run the agent (with the venv activated):

   ```bash
   python realtime_voice_agent.py
   ```

Optional env vars:

- `DEMO_SITE_NAME` — default `Memorial Demo Hospital`
- `MAX_SESSION_SECONDS` — default `300`

Use headphones in a live room to reduce speaker echo.

## Arize Skills Setup

Use this when demoing [Arize Skills](https://arize.com/docs/ax/skills/install) in Cursor (or another supported coding agent) against this repo. Complete **Setup** first so you have a `.venv`; install the AX CLI into that same environment.

1. **Install the AX CLI** (Python 3.11+; with the project venv activated):

   ```bash
   uv pip install arize-ax-cli
   ```

   Verify:

   ```bash
   ax --version
   ```

2. **Create and select a profile** so `ax` commands know how to reach your Arize org:

   ```bash
   ax profiles create
   ```

   The wizard prompts for an API key (same value as `ARIZE_API_KEY` in `.env`) and region. Non-interactive example:

   ```bash
   ax profiles create demo --api-key "$ARIZE_API_KEY" --region US
   ax profiles use demo
   ax profiles validate
   ```

   If you already filled in `.env` during **Setup**, many skills pick up `ARIZE_API_KEY` and `ARIZE_SPACE_ID` from that file during their prerequisite check. A profile is still recommended for CLI workflows (`ax traces`, `ax datasets`, and so on).

3. **Install skills into this repo** (from the repo root, with Cursor closed or after install so it rescans skills):

   ```bash
   ax skills install
   ```

   Choose **Cursor** when prompted, or install non-interactively:

   ```bash
   ax skills install --agent cursor --yes
   ```

   Skills land under `.cursor/skills/` in this project. Re-open the folder in Cursor and ask the agent to use a skill by name (for example, instrument this app with `arize-instrumentation`, or inspect traces with `arize-trace`).

   Full options (other agents, global install, overwrite): [AX Skills install docs](https://arize.com/docs/ax/skills/install).

## Live script (~2 minutes)

1. **Device lookup:** “Look up device serial MDV 7842 019.”  
   Expect console: `Handoff: Service Supervisor → Device Registry Agent`
2. **Case status:** “What’s the status of case 10482?”  
   Expect: `Handoff: Service Supervisor → Case Status Agent`
3. **Troubleshooting:** “The display flickers on boot on the visualization system — what should I check?”  
   Expect: `Handoff: Service Supervisor → Troubleshooting Agent`

After a specialist finishes speaking, the session resets to the **Service Supervisor** so the next user utterance is triaged again (see `RealtimeAudioEnd` handler in `realtime_voice_agent.py`).

Other sample serials: `MDV-2201-441`, `MDV-9910-002`. Cases: `CASE-10491`.

## Sample catalog (demo)

Edit devices, cases, and checklists in [`demo_catalog.py`](demo_catalog.py).

| Serial         | Product              | Case        |
|----------------|----------------------|-------------|
| MDV-7842-019   | Visualization System | CASE-10482  |
| MDV-2201-441   | Power Console        | CASE-10491  |
| MDV-9910-002   | Navigation Hub       | —           |
