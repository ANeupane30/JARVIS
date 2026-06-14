# 06 — Speaker (Text-to-Speech)

**File:** `jarvis/component/speaker.py`
**Status:** ✅ Working
**Library:** `pyttsx3` (offline, Windows SAPI5)
**Concurrency:** `multiprocessing` — TTS runs in a dedicated subprocess

---

## What This File Does

This file gives JARVIS a voice. It converts text into spoken audio using the system's
offline TTS engine (SAPI5 on Windows via `pyttsx3`), **without blocking** the main audio
capture or orchestration loop.

---

## Why a Separate Process?

`pyttsx3` on Windows wraps the Windows **SAPI5 COM** (Component Object Model) voice engine.
Two critical problems arise if you call it in the main process:

| Problem | Effect |
|---|---|
| `runAndWait()` is **blocking** | The main thread freezes while JARVIS speaks — it can't listen for the wake word |
| SAPI5 COM state goes stale after the first `runAndWait()` | Subsequent calls produce **no audio** (silent failure, no exception) |

**Solution:** run the TTS engine inside a `multiprocessing.Process`. This gives it a
completely isolated memory space and a fresh COM context on every utterance.

---

## Module-Level State

```python
speak_queue = multiprocessing.Queue()   # text messages sent to the TTS worker
stop_event  = multiprocessing.Event()   # signal to interrupt speaking mid-sentence
tts_process = None                      # handle to the worker subprocess
```

These three objects are **inter-process** primitives — they work across the process boundary
because they live in shared OS-managed memory.

---

## Functions

### `speak_worker(q, stop_sig)` — the subprocess body

```python
def speak_worker(q, stop_sig):
    while True:
        text = q.get(timeout=1)     # block until a text item arrives
        if text is None: break      # sentinel value → clean shutdown

        engine = pyttsx3.init()     # fresh COM object every utterance
        engine.setProperty("rate", 200)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)   # voice index 1 (female on most Windows installs)

        def on_word(name, location, length):
            if stop_sig.is_set():
                engine.stop()       # abort mid-sentence

        engine.connect('started-word', on_word)
        stop_sig.clear()            # reset interrupt flag for this utterance
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        del engine                  # release COM object
```

**Key design choices:**

| Choice | Reason |
|---|---|
| `engine = pyttsx3.init()` **inside the loop** | Re-initialises the COM SpVoice object on each call, avoiding the stale-state silent-audio bug |
| `pyttsx3.init()` inside an already-running process costs ~100–300 ms | Far cheaper than the 2–5 s process cold-start paid on the first call |
| `on_word` callback checks `stop_sig` | Allows `terminate_speaking()` to abort speech word-by-word |
| `del engine` | Explicitly releases the COM handle to prevent resource leaks |
| `text is None` sentinel | Clean way to signal the worker to exit without killing the process from outside |

---

### `prewarm()` — start the subprocess at launch

```python
def prewarm():
    global tts_process
    if tts_process is None or not tts_process.is_alive():
        tts_process = multiprocessing.Process(
            target=speak_worker,
            args=(speak_queue, stop_event),
            daemon=True,
        )
        tts_process.start()
```

Call this **once** at application startup (before the main loop). The subprocess starts
immediately and sits waiting on `q.get()`. When the first `speak()` call arrives,
there is **zero cold-start delay** — the process is already alive.

The `audio_orchestrator.py` calls `prewarm()` during its initialisation:
```python
device_stream = start_audio_stream(...)
prewarm()   # ← process warms up while the KWS model is loading
```

`daemon=True` means the worker process is killed automatically when the main process exits.
You don't need to call `.terminate()` explicitly on normal shutdown.

---

### `speak(response)` — enqueue text

```python
def speak(response):
    speak_queue.put(response)
```

Puts the text onto `speak_queue`. Returns immediately — the caller is never blocked.
The worker picks it up and speaks as soon as it finishes the previous utterance (if any).

---

### `terminate_speaking()` — interrupt and drain

```python
def terminate_speaking():
    stop_event.set()            # signals on_word() callback to abort current speech
    while True:
        try:
            speak_queue.get_nowait()    # drain any queued-but-not-yet-spoken items
        except:
            break
    # The process is NOT terminated — avoids 5s reload cost on next speak()
```

Call this when you want JARVIS to stop talking immediately — for example, when a new
wake word is detected while JARVIS is still responding.

> **Note:** The process stays alive. Only the current and pending utterances are cancelled.
> The next `speak()` call will work normally with no warm-up delay.

---

## Full Call Flow

```
App starts
    │
    ▼
prewarm()
    │  subprocess launched
    │  speak_worker() starts, blocks on q.get()
    ▼
Main loop running...
    │
    │  [wake word detected]
    ▼
speak("How can I help you")
    │  puts text on speak_queue
    ▼
speak_worker() unblocks
    │  pyttsx3.init() → engine created (~150ms)
    │  engine.say() + runAndWait() → JARVIS speaks
    ▼
speak_worker() loops back, blocks on q.get()
    │
    │  [new wake word while speaking]
    ▼
terminate_speaking()
    │  stop_event.set() → on_word() aborts engine mid-sentence
    │  speak_queue drained
    ▼
speak("How can I help you")   ← next cycle starts immediately
```

---

## Exported Interface

```python
from jarvis.component.speaker import speak, prewarm, terminate_speaking
```

| Export | Signature | Purpose |
|---|---|---|
| `prewarm()` | `() → None` | Call once at startup to start the TTS subprocess |
| `speak(response)` | `(str) → None` | Enqueue text for speaking; non-blocking |
| `terminate_speaking()` | `() → None` | Abort current speech and drain queue |
| `speak_worker(q, stop_sig)` | internal | TTS subprocess body — do not call directly |

---

## Known Limitations / Future Improvements

| Issue | Detail |
|---|---|
| Voice index hardcoded | `voices[1].id` assumes index 1 is the preferred voice. Should be configurable via `config/`. |
| Speech rate hardcoded | `rate=200` is hardcoded. Should move to config. |
| No speak completion signal | `speak()` returns immediately; there is no way for the caller to know when speech finished. A `speak_and_wait()` variant with an Event would solve this. |
| Single worker | Only one utterance plays at a time. If `speak()` is called rapidly, items queue up rather than being spoken in parallel (which is actually correct behaviour for a voice assistant). |
