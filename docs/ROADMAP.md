# JARVIS — Project Roadmap

A personal AI voice assistant inspired by Iron Man's JARVIS.
This roadmap tracks what has been completed, what is in progress, and what is planned next.

---

## ✅ Phase 1 — Project Foundation
> Setting up the project structure, environment, and tooling.

- [x] Initialize Git repository
- [x] Set up Python virtual environment (`.venv`)
- [x] Create `requirements.txt` with all dependencies
- [x] Set up `.env` and `.env.example` for environment variables (`BOT_NAME`, `USER_NAME`)
- [x] Create folder structure (`core/`, `modules/`, `integrations/`, `interface/`, `config/`, `docs/`, `tests/`, `scripts/`)
- [x] Write setup scripts for Windows (`scripts/setup.ps1`) and Linux/macOS (`scripts/setup.sh`)
- [x] Write `docs/setup.md` — installation and configuration guide
- [x] Write `docs/guide.md` — library reference and tool decisions

---

## ✅ Phase 2 — Voice Input Pipeline
> Getting JARVIS to hear and understand the user.

- [x] **Microphone Listener** (`modules/voice/listener.py`)
  - Captures raw audio using `sounddevice`
  - Runs a background thread continuously pushing 30ms audio chunks into a thread-safe queue
  - Configurable via `config/sounddevice.config` (sample rate, channels, block duration)

- [x] **Wake Word Detection** (`modules/voice/wakeup.py`)
  - Integrates `sherpa-onnx` KeywordSpotter with a Zipformer model (3.3M params, trained on GigaSpeech)
  - Reads model paths and tuning parameters from `config/sherpa_onnx.config`
  - Pulls audio from the listener queue, feeds it to the KWS stream, and prints on keyword detection
  - Resets the KWS stream after each detection to stay ready for the next trigger

- [x] **Speech-to-Text** (`modules/voice/speech_to_text.py`)
  - Uses `faster-whisper` (`base` model, CPU) to transcribe audio bytes into text
  - Accepts raw audio as bytes via `io.BytesIO` and returns the transcribed string

- [x] **KWS Model downloaded** (`sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/`)
  - Encoder, decoder, joiner, tokens, and keywords file all present locally

---

## 🔲 Phase 3 — Voice Output
> Getting JARVIS to speak back to the user.

- [ ] **Text-to-Speech Speaker** (`modules/voice/speaker.py`)
  - Implement TTS using `pyttsx3` (offline, no internet required)
  - Expose a simple `speak(text)` function
  - Support configurable voice rate and volume

---

## 🔲 Phase 4 — Brain / Intelligence
> Connecting JARVIS to an LLM for reasoning and conversation.

- [ ] **LLM Integration** (`modules/brain/llm.py`)
  - Connect to a language model (local or API-based)
  - Send transcribed user input and receive a response

- [ ] **Memory System** (`modules/brain/memory.py`)
  - Implement short-term conversation history (context window)
  - Consider long-term memory storage for user preferences

---

## 🔲 Phase 5 — Orchestration
> Wiring all modules together into one continuous loop.

- [ ] **Core Orchestrator** (`core/orchestrator.py`)
  - Build the main event loop:
    1. Listen → detect wake word
    2. Capture user speech
    3. Transcribe speech to text
    4. Send text to LLM brain
    5. Speak the LLM response back

- [ ] **Main Entry Point** (`main.py`)
  - Initialize all modules
  - Start the orchestrator loop
  - Handle graceful shutdown (e.g., `Ctrl+C`)

---

## 🔲 Phase 6 — Skills
> Adding specific capabilities JARVIS can perform.

- [ ] Design a skill system / plugin architecture (`modules/skills/`)
- [ ] Implement starter skills (e.g., time/date, open apps, web search)
- [ ] Connect skills to the orchestrator via intent detection

---

## 🔲 Phase 7 — Integrations & Interface
> Connecting JARVIS to external services and adding a UI.

- [ ] External API integrations (`integrations/`)
  - HTTP calls via `httpx`
  - Examples: weather, news, calendar

- [ ] User interface (`interface/`)
  - Optional visual interface (GUI or web dashboard)

---

## 🔲 Phase 8 — Testing & Quality
> Making sure everything works reliably.

- [ ] Write unit tests (`tests/unit/`)
- [ ] Write integration tests (`tests/integration/`)
- [ ] Add test audio samples (stub `.wav` files already present in `tests/`)
- [ ] Set up CI/CD or a test runner script

---

## Notes
- The `integrations/` and `interface/` directories are created but intentionally left empty until later phases.
- `pyttsx3` is already installed; `speaker.py` is the next priority file to implement.
- Libraries previously considered but replaced: `vosk`, `SpeechRecognition`, `python-decouple`, `requests` — see `docs/guide.md` for details.
