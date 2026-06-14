# JARVIS

A personal AI voice assistant inspired by JARVIS from Iron Man, built entirely in Python with fully offline voice I/O.

## What It Does (Current State)
- 🎤 Captures real-time audio from your microphone
- 🔍 Detects a wake word offline using `sherpa-onnx` (Zipformer KWS model)
- 🗣️ Says "How can I help you" using `pyttsx3` (offline TTS)
- 📝 Transcribes your voice command using `faster-whisper` (offline STT)
- 🧠 LLM integration is the next milestone

## Getting Started
For detailed setup instructions, see the **[Setup Guide](docs/setup.md)**.

## Project Documentation
| Document | Description |
|---|---|
| [docs/setup.md](docs/setup.md) | Installation and configuration guide |
| [docs/guide.md](docs/guide.md) | Library reference and tool decisions |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What's done and what's planned |
| [docs/user_guide/](docs/user_guide/) | Deep technical guides for each module |

## Quick Start
```bash
# Activate your virtual environment
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS/Linux

# Run JARVIS
python main.py
```
Press `Ctrl+C` to stop safely.
