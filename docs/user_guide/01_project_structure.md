# 01 — Project Structure

This document explains the folder layout of JARVIS and the purpose of each directory.

---

## Top-Level Layout

```
JARVIS/
├── main.py                  ← Entry point (empty — not yet implemented)
├── requirements.txt         ← All pip dependencies
├── .env                     ← Your personal secrets (BOT_NAME, USER_NAME) — NOT committed to git
├── .env.example             ← Template showing what .env should contain
├── .gitignore               ← Tells git to ignore .env and .venv
│
├── config/                  ← Configuration files (not secrets, safe to commit)
├── core/                    ← The orchestrator that connects all modules
├── modules/                 ← Core feature modules (voice, brain, skills)
├── integrations/            ← Future: external API connections
├── interface/               ← Future: GUI or web dashboard
├── docs/                    ← All documentation
├── tests/                   ← Unit and integration tests
├── scripts/                 ← One-time setup scripts
└── sherpa-onnx-kws-.../     ← The downloaded KWS model files (local, not committed)
```

---

## Directory Breakdown

### `config/`
Stores non-secret settings in `.config` (INI-format) files. Read at runtime using Python's
built-in `configparser`. Two files exist:

| File | Used by |
|---|---|
| `sounddevice.config` | `listener.py` — audio capture settings |
| `sherpa_onnx.config` | `wakeup.py` — KWS model settings |

Why config files instead of hardcoding? So you can change settings (e.g., sample rate,
detection threshold) without touching the Python source code.

---

### `core/`
Contains `orchestrator.py` — the future brain that will connect all modules into one loop:
listen → detect → transcribe → think → speak. Currently empty.

---

### `modules/`
The main feature code. Split into three sub-folders:

```
modules/
├── voice/      ← Everything related to audio (input and output)
│   ├── listener.py         ✅ Working — mic capture
│   ├── wakeup.py           ✅ Working — wake word detection
│   ├── speech_to_text.py   ✅ Working — Whisper transcription
│   └── speaker.py          🔲 Empty  — text-to-speech (planned)
│
├── brain/      ← LLM reasoning and memory
│   ├── llm.py              🔲 Empty  — LLM connection (planned)
│   └── memory.py           🔲 Empty  — conversation history (planned)
│
└── skills/     ← Specific capabilities JARVIS can perform
    └── skill1.py           🔲 Empty  — placeholder (planned)
```

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

### `sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/`
The actual AI model files downloaded locally. Contains:
- `encoder-*.onnx` — the encoder part of the Zipformer model
- `decoder-*.onnx` — the decoder
- `joiner-*.onnx` — combines encoder + decoder outputs
- `tokens.txt` — maps model output indices to characters
- `keywords.txt` — the list of wake words the model should listen for
