# JARVIS

A personal AI voice assistant inspired by JARVIS from Iron Man, built entirely in Python with fully offline voice I/O and cloud LLM reasoning.

## What It Does (Current State)
- 🎤 Captures real-time audio from your microphone
- 🔍 Detects a wake word offline using `sherpa-onnx` (Zipformer KWS model)
- 🗣️ Says "How can I help you" using `pyttsx3` (offline TTS)
- 📝 Transcribes your voice command using `faster-whisper` (offline STT)
- 🧠 Sends your transcript to an LLM via **OpenRouter API** (`openai/o4-mini`) and speaks the response
- 🔧 **MCP (Model Context Protocol)** infrastructure implemented — client + server with tool-calling support

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
# Activate your virtual environment (project uses uv)
uv sync                              # Install dependencies

# Activate the venv
.venv\Scripts\activate               # Windows
source .venv/bin/activate            # macOS/Linux

# Run JARVIS
python main.py
```
Press `Ctrl+C` to stop safely.

## Environment Variables
Copy `.env.example` to `.env` and fill in:
```
BOT_NAME=JARVIS
USER_NAME=YourName
OPENROUTER_API_KEY=your_key_here
```
