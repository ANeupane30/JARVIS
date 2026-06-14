# 07 — Audio Orchestrator

**Files:**
- `jarvis/orchestrator/audio_orchestrator.py` — production run loop
- `jarvis/orchestrator/test_orchestrator.py` — diagnostic run loop with timing and state logging

**Status:** ✅ Working
**Depends on:** `listener.py`, `wakeup.py`, `transcriber.py`, `speaker.py`

---

## What This Module Does

The orchestrator is the **conductor** — it wires all four components together into a
continuous voice interaction loop:

```
Mic → [KWS] → flush queue → speak greeting → [STT] → print transcript → repeat
```

It owns:
- Starting the microphone stream (once, at startup)
- Prewarming the TTS process (once, at startup)
- Running the main event loop
- Graceful shutdown on `KeyboardInterrupt`

---

## `audio_orchestrator.py` — Production Orchestrator

### Startup

```python
config = configparser.ConfigParser()
config.read("config/sounddevice.config")

sample_rate    = int(config['kws_audio']['SAMPLE_RATE'])
block_duration = float(config['kws_audio']['BLOCK_DURATION'])
channels       = int(config['kws_audio']['CHANNELS'])
```

Audio parameters are read once at module import from `config/sounddevice.config`.
The same config section (`[kws_audio]`) is used by `wakeup.py`.

### `run()` — Main Loop

```python
def run():
    device_stream = start_audio_stream(sample_rate, channels, block_duration)
    prewarm()           # TTS subprocess starts here, while KWS model loads below
    print('Listening....')

    try:
        while True:
            keyword = kws()                        # STEP 1: block until wake word
            print("KWS Detected")
            speak("How can I help you")            # STEP 2: non-blocking speak

            while not audio_queue.empty():         # STEP 3: flush wake-word audio
                try: audio_queue.get_nowait()
                except q.Empty: break

            transcript = listen_and_transcribe(block_duration)  # STEP 4: STT
            print(f"You said: {transcript}")

    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        device_stream.stop()
        device_stream.close()
```

#### Step-by-step

| Step | What happens | Why |
|---|---|---|
| `start_audio_stream()` | Mic stream started once | Never restarted — stream runs continuously for both KWS and STT |
| `prewarm()` | TTS subprocess launched | Starts while KWS model loads in `wakeup.py` import — hides cold-start latency |
| `kws()` | Blocks until wake word detected | Reads `audio_queue` continuously |
| `speak("How can I help you")` | Enqueues greeting text | Non-blocking — TTS worker handles it asynchronously |
| Queue flush | Discards wake-word audio | Prevents Whisper from transcribing "Hey JARVIS" as the user command |
| `listen_and_transcribe()` | Records until silence, then transcribes | Uses the same `audio_queue` as KWS |
| `print(transcript)` | Outputs the result | Future: will be sent to `llm.py` |

#### Why the queue flush matters

After wake word detection, `audio_queue` still contains the audio of the wake word itself
("Hey JARVIS"). If not flushed, `listen_and_transcribe()` would pick it up and Whisper
would transcribe it as the start of the user's command. The flush discards these stale chunks.

#### Graceful shutdown

`finally:` ensures the PortAudio stream is always properly closed even if an exception
occurs, preventing microphone resource leaks.

---

## `test_orchestrator.py` — Diagnostic Orchestrator

This file is a **drop-in replacement** for `audio_orchestrator.py` used during debugging.
It runs the same pipeline but wraps every step with detailed logging.

### Purpose

When diagnosing issues like:
- TTS process dying silently
- Whisper starting while JARVIS is still speaking
- Queue build-up causing lag
- `speak_and_wait()` timing out prematurely

### Helper Functions

#### `log(cycle, step, detail)`
```python
def log(cycle: int, step: str, detail: str = ""):
    ms = int(time.time() * 1000) % 1000
    ts = time.strftime('%H:%M:%S.') + f"{ms:03d}"
    print(f"[{ts}] C{cycle} | {step:<38} {detail}")
```
Prints a timestamped line with cycle number, step name, and extra detail.
Format: `[HH:MM:SS.mmm] C<N> | <step>                      <detail>`

#### `tts_state() → str`
```python
def tts_state() -> str:
    proc      = speaker.tts_process
    alive     = proc is not None and proc.is_alive()
    pid       = proc.pid if proc is not None else "none"
    event_set = speaker.event.is_set()
    qsize     = speaker.speak_queue.qsize()
    return f"process={'ALIVE' if alive else 'DEAD '} pid={str(pid):<6} | event={'SET  ' if event_set else 'CLEAR'} | speak_q={qsize}"
```
Snapshot of the TTS subprocess state. Useful for detecting:
- `DEAD` → process crashed or was killed
- `event=SET` → `terminate_speaking()` was called but not cleared yet
- `speak_q > 0` → items waiting to be spoken

#### `audio_state() → str`
```python
def audio_state() -> str:
    return f"audio_queue={audio_queue.qsize()}"
```
Shows how many audio chunks are currently waiting in the queue.
Large values indicate a lag or that the queue wasn't flushed.

#### `divider(cycle, label)`
Prints a visual separator between cycles for easy log scanning.

### `run()` — Diagnostic Loop

The test run loop executes these steps in order each cycle:

| Step | Code | What it checks |
|---|---|---|
| 1 — KWS | `kws()` | Wake word latency |
| 2 — Terminate previous speech | `terminate_speaking()` | Whether interrupt works cleanly |
| 3 — Flush queue | drain `audio_queue` | How many stale chunks were present |
| 4 — Speak and wait | `speak_and_wait(GREETING)` | TTS timing, process alive after speak |
| 4b — Sleep 0.3s | `time.sleep(0.3)` | Checks if process is still alive 300ms after speaking |
| 5 — STT | `listen_and_transcribe()` | Transcript content and duration |

Each step is logged before and after with `tts_state()` and `audio_state()` so you can
see exactly what the system state was at each moment.

> **Note:** `test_orchestrator.py` references `speaker.speak_and_wait()` and `speaker.mp_running()`
> which are planned but not yet fully implemented in `speaker.py`. These will need to be
> added to `speaker.py` before `test_orchestrator.py` can run without errors.

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Single shared `audio_queue` for both KWS and STT | Simplest architecture — no need to copy audio or manage two streams |
| Stream started once, never restarted | Restarting `sounddevice` streams introduces ~100ms gaps; continuous stream is seamless |
| `prewarm()` called before the loop | Hides TTS cold-start latency behind KWS model loading time |
| Queue flush after KWS detection | Prevents wake-word audio leaking into STT |
| `test_orchestrator.py` as separate file | Keeps production code clean while enabling detailed diagnostics without modifying `audio_orchestrator.py` |

---

## Entry Point

`main.py` imports from the production orchestrator:
```python
from jarvis.orchestrator.audio_orchestrator import run

if __name__ == '__main__':
    run()
```

To use the test orchestrator, change the import to:
```python
from jarvis.orchestrator.test_orchestrator import run
```

---

## Future: Full Brain Loop

Once `jarvis/brain/llm.py` is implemented, the orchestrator loop will extend to:

```python
while True:
    keyword    = kws()
    speak("How can I help you")
    flush_queue()
    transcript = listen_and_transcribe(block_duration)
    response   = llm.generate(transcript)       # ← Phase 5
    speak(response)                             # ← Phase 6
```
