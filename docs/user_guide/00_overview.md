# JARVIS — Technical Guide Index

This folder contains technical documentation written for the developer (you) to understand
exactly what each part of the project does, how it works, and how the pieces connect.

## Who is this for?
You — the developer. These guides explain the internal logic of the code in plain language
so you can come back after a break and immediately understand what's happening.

---

## Guide Files

| File | What it covers |
|---|---|
| [01_project_structure.md](01_project_structure.md) | Folder layout and what each directory is for |
| [02_audio_listener.md](02_audio_listener.md) | How the microphone is captured (`listener.py`) |
| [03_wake_word_detection.md](03_wake_word_detection.md) | How the wake word is detected (`wakeup.py`) |
| [04_speech_to_text.md](04_speech_to_text.md) | How speech is converted to text (`speech_to_text.py`) |
| [05_configuration.md](05_configuration.md) | How config files work and what each setting does |

---

## Current Data Flow (What Works Today)

```
Microphone
    │
    ▼
listener.py  ──►  audio_queue (thread-safe Queue)
                        │
                        ▼
                  wakeup.py  ──►  sherpa-onnx KWS model
                                        │
                                  Keyword detected?
                                        │
                              ┌─────── YES ──────┐
                              │                  │
                              ▼                  ▼
                    [Future] capture      print "KEYWORD DETECTED"
                    user command          reset KWS stream
                              │
                              ▼
                    speech_to_text.py  ──►  faster-whisper
                              │
                              ▼
                    [Future] send text to LLM brain
```

> **Note:** Everything below "Keyword detected?" is not yet wired up.
> `speech_to_text.py` exists but is not yet called from `wakeup.py`.
