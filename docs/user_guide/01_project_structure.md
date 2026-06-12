# 01 — Project Structure

This document explains the folder layout of JARVIS and the purpose of each directory.

---

## Top-Level Layout

```
JARVIS/
├── main.py                  ← Entry point — imports and runs the audio orchestrator
├── requirements.txt         ← All pip dependencies
├── .env                     ← Your personal secrets (BOT_NAME, USER_NAME) — NOT committed to git
├── .env.example             ← Template showing what .env should contain
├── .gitignore               ← Tells git to ignore .env and .venv
│
├── jarvis/                  ← Main Python package (all source code lives here)
├── config/                  ← Configuration files (not secrets, safe to commit)
├── model/                   ← Downloaded AI model files (not committed to git)
├── integrations/            ← Future: external API connections
├── interface/               ← Future: GUI or web dashboard
├── docs/                    ← All documentation
├── tests/                   ← Unit and integration tests
└── scripts/                 ← One-time setup scripts
```

---

## Directory Breakdown

### `jarvis/` — The Main Python Package

This is the heart of the project. All source code is inside this package.
Importing works via `from jarvis.component.listener import ...` etc.

```
jarvis/
├── __init__.py
│
├── component/              ← Low-level hardware/IO modules
│   ├── __init__.py
│   ├── listener.py         ✅ Working — microphone capture via sounddevice
│   ├── wakeup.py           ✅ Working — wake word detection via sherpa-onnx
│   ├── transcriber.py      ✅ Working — silence-aware STT via faster-whisper
│   └── speaker.py          ✅ Working — offline TTS via pyttsx3 (multiprocess)
│
├── orchestrator/           ← Wires components into a single run loop
│   ├── __init__.py
│   └── audio_orchestrator.py  ✅ Working — main event loop
│
├── brain/                  ← LLM reasoning and memory (planned)
│   ├── llm.py              🔲 Empty — LLM connection (planned)
│   ├── memory.py           🔲 Empty — conversation history (planned)
│   └── response.py         🔲 Empty — response post-processing (planned)
│
└── skills/                 ← Specific capabilities JARVIS can perform (planned)
    └── example1_skill1.py  🔲 Placeholder
```

---

### `config/`
Stores non-secret settings in `.config` (INI-format) files. Read at runtime using Python's
built-in `configparser`. Two files exist:

| File | Used by | Config section |
|---|---|---|
| `sounddevice.config` | `listener.py`, `audio_orchestrator.py` | `[kws_audio]` |
| `sherpa_onnx.config` | `wakeup.py` | `[kws]` |

> **Important:** The config section in `sounddevice.config` is `[kws_audio]` (not `[audio]`).
> Both `wakeup.py` and `audio_orchestrator.py` read from this section.

Why config files instead of hardcoding? So you can change settings (e.g., sample rate,
detection threshold) without touching the Python source code.

---

### `model/`
Contains the downloaded AI model files. Not committed to git (large binary files).

```
model/
└── kws-zipformer/          ← Sherpa-ONNX Zipformer KWS model (GigaSpeech, 3.3M params)
    ├── encoder-epoch-12-avg-2-chunk-16-left-64.onnx
    ├── decoder-epoch-12-avg-2-chunk-16-left-64.onnx
    ├── joiner-epoch-12-avg-2-chunk-16-left-64.onnx
    ├── tokens.txt
    └── keywords.txt
```

Paths to these files are configured in `config/sherpa_onnx.config`.

---

### `integrations/`
Empty for now. Will hold code to talk to external APIs (weather, news, calendar, etc.)
using `httpx`.

---

### `interface/`
Empty for now. Will hold any visual interface — could be a terminal UI, a desktop GUI,
or a local web dashboard.

---

### `docs/`
All documentation for the project.

```
docs/
├── setup.md         ← How to install and run the project
├── guide.md         ← Library reference and tool decision notes
├── ROADMAP.md       ← What's done, what's next
└── user_guide/      ← This folder — deep technical guides per module
    ├── 00_overview.md
    ├── 01_project_structure.md
    ├── 02_audio_listener.md
    ├── 03_wake_word_detection.md
    ├── 04_speech_to_text.md
    └── 05_configuration.md
```

---

### `tests/`
```
tests/
├── unit/               ← Tests for individual functions in isolation (empty)
├── integration/        ← Tests for multiple modules working together (empty)
├── activation.wav      ← Sample audio file for testing
└── python_example_test.wav  ← Another sample audio file
```

---

### `scripts/`
One-time setup helpers:
- `setup.ps1` — Windows PowerShell setup script
- `setup.sh` — macOS/Linux shell setup script

---

### `main.py`
The project entry point. Minimal by design:
```python
from jarvis.orchestrator.audio_orchestrator import run

if __name__ == '__main__':
    test = run()
```
Run with: `python main.py`
