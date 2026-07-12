# 01 — Project Structure

This document explains the folder layout of JARVIS and the purpose of each directory.

---

## Top-Level Layout

```
JARVIS/
├── main.py                  ← Entry point — DLL fix + runs the audio orchestrator
├── test.py                  ← Scratch test file (not part of main pipeline)
├── pyproject.toml           ← Project metadata and all dependencies (uv-managed)
├── uv.lock                  ← Locked dependency versions (committed to git)
├── .env                     ← Your personal secrets (BOT_NAME, USER_NAME, OPENROUTER_API_KEY) — NOT committed to git
├── .env.example             ← Template showing what .env should contain
├── .python-version          ← Specifies Python version for uv/pyenv (3.12)
├── .gitignore               ← Tells git to ignore .env and .venv
│
├── jarvis/                  ← Main Python package (all source code lives here)
├── mcp_server/              ← MCP (Model Context Protocol) server
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
├── component/                    ← Low-level hardware/IO modules
│   ├── __init__.py
│   ├── listener.py               ✅ Working — microphone capture via sounddevice
│   ├── wakeup.py                 ✅ Working — wake word detection via sherpa-onnx
│   ├── transcriber.py            ✅ Working — silence-aware STT via faster-whisper
│   ├── speaker.py                ✅ Working — offline TTS via pyttsx3 (multiprocess)
│   └── response_formatter.py    ✅ Working — parses OpenRouter JSON to plain text
│
├── orchestrator/                 ← Wires components into a single run loop
│   ├── __init__.py
│   ├── audio_orchestrator.py    ✅ Working — production main event loop (KWS→STT→LLM→TTS)
│   └── test_orchestrator.py     ✅ Working — diagnostic loop with timing/state logs
│
├── brain/                        ← LLM reasoning and memory
│   ├── llm.py                   ✅ Working — OpenRouter API (openai/o4-mini)
│   ├── mcp_client.py            ✅ Implemented — MCP client (not yet wired into loop)
│   ├── memory.py                🔲 Empty — conversation history (planned)
│   └── response.py              🔲 Empty — response post-processing (planned)
│
└── skills/                       ← Specific capabilities JARVIS can perform (planned)
    └── example1_skill1.py       🔲 Placeholder
```

---

### `mcp_server/` — Model Context Protocol Server

Implements the server side of the MCP tool-use protocol. Runs as a subprocess and
communicates with the MCP client in `jarvis/brain/mcp_client.py` over stdio.

```
mcp_server/
└── server.py    ✅ Implemented — exposes get_weather tool (stub data, real integration planned)
```

---

### `config/`
Stores non-secret settings in `.config` (INI-format) files. Read at runtime using Python's
built-in `configparser`. Two files exist:

| File | Used by | Config section |
|---|---|---|
| `sounddevice.config` | `listener.py`, `audio_orchestrator.py`, `test_orchestrator.py` | `[kws_audio]` |
| `sherpa_onnx.config` | `wakeup.py` | `[kws]`, `[kws_audio]` |

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
or a local web dashboard (via `starlette` + `uvicorn`, already in dependencies).

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
    ├── 05_configuration.md
    ├── 06_speaker.md
    ├── 07_audio_orchestrator.md
    └── 08_brain.md              ← NEW: LLM, MCP client, response formatter
```

---

### `tests/`
```
tests/
├── unit/               ← Tests for individual functions in isolation (empty)
├── integration/        ← Tests for multiple modules working together (empty)
├── activation.wav      ← Sample audio file for wake word testing
└── python_example_test.wav  ← Sample audio file for STT testing
```

---

### `scripts/`
One-time setup helpers:
- `setup.ps1` — Windows PowerShell setup script
- `setup.sh` — macOS/Linux shell setup script

---

### `main.py`
The project entry point. Handles a critical Windows DLL loading order issue before any imports:

```python
import os, sys
from pathlib import Path

if sys.platform == "win32":
    import importlib.util
    for pkg in ("onnxruntime", "sherpa_onnx"):
        spec = importlib.util.find_spec(pkg)
        if spec and spec.origin:
            base = Path(spec.origin).parent
            for sub in ("", "capi", "lib"):
                d = base / sub
                if d.exists():
                    os.add_dll_directory(str(d))
                    os.environ["PATH"] = str(d) + os.pathsep + os.environ["PATH"]

import onnxruntime  # preload the venv's 1.27 DLL before sherpa can touch System32's

from jarvis.orchestrator.audio_orchestrator import run

if __name__ == '__main__':
    run()
```

**Why the DLL preload?** Windows has two copies of `onnxruntime.dll` — one in the venv
and one in System32 (installed by other software). `sherpa_onnx` requires the venv's newer
version. By explicitly adding the venv's directories to the DLL search path and importing
`onnxruntime` first, we guarantee the correct version is loaded before `sherpa_onnx` touches
the DLL loader.

Run with: `python main.py`
