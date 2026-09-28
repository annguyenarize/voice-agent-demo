# Medical device field-service voice agent (multi-agent)

Synthetic sample data only. Not connected to production systems.

A **Service Supervisor** routes each request to a specialist agent. Each specialist has access to only its own tools:

| Agent | Tool |
|-------|------|
| Device Registry Agent | `lookup_device` |
| Case Status Agent | `get_service_case` |
| Troubleshooting Agent | `get_troubleshooting_guide` |

Agent definitions and handoffs live in [`voice_agents.py`](voice_agents.py). Tools and catalog wiring live in [`demo_tools.py`](demo_tools.py) and [`demo_catalog.py`](demo_catalog.py).

## Setup

```bash
source .venv/bin/activate
# OPENAI_API_KEY in .env
python realtime_voice_agent.py
```

Optional env vars:

- `DEMO_SITE_NAME` — default `Memorial Demo Hospital`
- `MAX_SESSION_SECONDS` — default `300`

Use headphones in a live room to reduce speaker echo.

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
