#!/usr/bin/env python3
"""
Multi-agent field-service voice demo (OpenAI Agents SDK).

A supervisor agent routes to specialists; each specialist has its own tools.

Synthetic demo data only.

Requires a microphone and speaker. Set OPENAI_API_KEY (e.g. in .env), then:

  python realtime_voice_agent.py

Session stays open for multiple turns until Ctrl+C or the time limit.
"""

from __future__ import annotations

import asyncio
import os
import time

import numpy as np
import sounddevice as sd
from agents.realtime import RealtimeRunner
from agents.realtime.config import RealtimeRunConfig
from agents.realtime.events import (
    RealtimeAudio,
    RealtimeAudioEnd,
    RealtimeAudioInterrupted,
    RealtimeHandoffEvent,
    RealtimeToolStart,
)
from dotenv import load_dotenv
from voice_agents import build_agent_graph

load_dotenv()

SAMPLE_RATE = 24_000
CHANNELS = 1
MIC_CHUNK_FRAMES = 1_200
MAX_SESSION_SECONDS = int(os.environ.get("MAX_SESSION_SECONDS", "300"))
POST_PLAYBACK_MIC_COOLDOWN_S = float(os.environ.get("POST_PLAYBACK_MIC_COOLDOWN_S", "0.35"))

REALTIME_CONFIG: RealtimeRunConfig = {
    "model_settings": {
        "audio": {
            "input": {
                "noise_reduction": {"type": "near_field"},
                "turn_detection": {
                    "type": "semantic_vad",
                    "interrupt_response": False,
                    "eagerness": "low",
                },
            },
            "output": {
                "speed": 1.25,
            },
        },
    },
}


def print_demo_runbook() -> None:
    print("Multi-agent field service demo (supervisor + specialists). Sample data only.\n")
    print(f"Time limit: {MAX_SESSION_SECONDS}s (MAX_SESSION_SECONDS). Ctrl+C to end.\n")
    print("Suggested demo script:")
    print('  1. "Look up device serial MDV 7842 019."  → Device Registry Agent')
    print('  2. "What\'s the status of case 10482?"  → Case Status Agent')
    print('  3. "The display flickers on boot on the visualization system — what should I check?"')
    print("     → Troubleshooting Agent\n")
    print("Watch the console for Handoff: lines between agents.\n")
    print("Tip: use headphones if playback cuts out (speaker echo).\n")


def make_mic_callback(mic_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Forward mic chunks into an asyncio queue."""

    def cb(indata, frames, _time, status):
        if status:
            print(f"Mic: {status}")
        chunk = indata.copy().tobytes()
        loop.call_soon_threadsafe(mic_queue.put_nowait, chunk)

    return cb


async def run_session() -> None:
    loop = asyncio.get_running_loop()
    mic_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    stop = asyncio.Event()

    async def hard_timer():
        await asyncio.sleep(MAX_SESSION_SECONDS)
        print(f"\nSession limit ({MAX_SESSION_SECONDS}s) reached.")
        stop.set()

    starting_agent = build_agent_graph()
    runner = RealtimeRunner(starting_agent, config=REALTIME_CONFIG)
    async with await runner.run() as session:
        print_demo_runbook()

        assistant_playing = False
        mic_mute_until = 0.0

        def mic_send_enabled() -> bool:
            return not assistant_playing and time.monotonic() >= mic_mute_until

        def drain_mic_queue() -> None:
            while True:
                try:
                    mic_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        async def send_mic():
            while not stop.is_set():
                if not mic_send_enabled():
                    drain_mic_queue()
                    await asyncio.sleep(0.05)
                    continue
                try:
                    chunk = await asyncio.wait_for(mic_queue.get(), timeout=0.1)
                    await session.send_audio(chunk)
                except asyncio.TimeoutError:
                    continue

        timer_task = asyncio.create_task(hard_timer())
        send_task = asyncio.create_task(send_mic())
        events_task = None

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=MIC_CHUNK_FRAMES,
                callback=make_mic_callback(mic_queue, loop),
            ), sd.OutputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=MIC_CHUNK_FRAMES,
            ) as out_stream:

                async def handle_events():
                    nonlocal assistant_playing, mic_mute_until
                    active_agent = starting_agent
                    supervisor_reset_task: asyncio.Task | None = None

                    async def schedule_supervisor_reset() -> None:
                        nonlocal supervisor_reset_task, active_agent
                        if supervisor_reset_task is not None and not supervisor_reset_task.done():
                            supervisor_reset_task.cancel()
                        async def _reset_after_speech():
                            await asyncio.sleep(0.75)
                            nonlocal active_agent
                            if active_agent is not starting_agent:
                                await session.update_agent(starting_agent)
                                active_agent = starting_agent
                                print("Active agent reset → Service Supervisor")

                        supervisor_reset_task = asyncio.create_task(_reset_after_speech())

                    async for event in session:
                        if stop.is_set():
                            break
                        if isinstance(event, RealtimeHandoffEvent):
                            active_agent = event.to_agent
                            print(
                                f"Handoff: {event.from_agent.name} → {event.to_agent.name}"
                            )
                        elif isinstance(event, RealtimeToolStart):
                            print(
                                f"Tool: {event.agent.name} → {event.tool.name}"
                            )
                        elif isinstance(event, RealtimeAudio):
                            # Supervisor only routes in the background; do not play its audio.
                            if active_agent is starting_agent:
                                continue
                            assistant_playing = True
                            if (
                                supervisor_reset_task is not None
                                and not supervisor_reset_task.done()
                            ):
                                supervisor_reset_task.cancel()
                            arr = np.frombuffer(event.audio.data, dtype=np.int16)
                            await loop.run_in_executor(None, out_stream.write, arr)
                        elif isinstance(event, RealtimeAudioEnd):
                            if active_agent is starting_agent:
                                continue
                            assistant_playing = False
                            mic_mute_until = time.monotonic() + POST_PLAYBACK_MIC_COOLDOWN_S
                            drain_mic_queue()
                            if active_agent is not starting_agent:
                                await schedule_supervisor_reset()
                        elif isinstance(event, RealtimeAudioInterrupted):
                            assistant_playing = False
                            mic_mute_until = time.monotonic() + POST_PLAYBACK_MIC_COOLDOWN_S
                            drain_mic_queue()
                            await loop.run_in_executor(None, out_stream.abort)
                            await loop.run_in_executor(None, out_stream.start)

                events_task = asyncio.create_task(handle_events())
                await stop.wait()
        except KeyboardInterrupt:
            print("\nInterrupted.")
            stop.set()
        finally:
            pending = [t for t in (timer_task, send_task, events_task) if t is not None]
            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    print("Session ended.")


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Missing environment variable: OPENAI_API_KEY")

    asyncio.run(run_session())


if __name__ == "__main__":
    main()
