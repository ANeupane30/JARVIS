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
- [x] Create folder structure (`jarvis/`, `jarvis/component/`, `jarvis/orchestrator/`, `jarvis/brain/`, `jarvis/skills/`, `config/`, `model/`, `docs/`, `tests/`, `scripts/`, `integrations/`, `interface/`)
- [x] Write setup scripts for Windows (`scripts/setup.ps1`) and Linux/macOS (`scripts/setup.sh`)
- [x] Write `docs/setup.md` — installation and configuration guide
- [x] Write `docs/guide.md` — library reference and tool decisions

---

## ✅ Phase 2 — Voice Input Pipeline
> Getting JARVIS to hear and understand the user.

- [x] **Microphone Listener** (`jarvis/component/listener.py`)
  - Captures raw audio using `sounddevice`
  - Runs a background thread continuously pushing 30ms audio chunks into a thread-safe queue
  - Configurable via `config/sounddevice.config` (sample rate, channels, block duration)
  - Exports `audio_queue` (shared Queue) and `start_audio_stream()` function

- [x] **Wake Word Detection** (`jarvis/component/wakeup.py`)
  - Integrates `sherpa-onnx` KeywordSpotter with a Zipformer model (3.3M params, trained on GigaSpeech)
  - Reads model paths and tuning parameters from `config/sherpa_onnx.config`
  - Pulls audio from the listener queue, feeds it to the KWS stream
  - Returns `True` when wake word is detected; caller resets and re-invokes

- [x] **Speech-to-Text / Transcriber** (`jarvis/component/transcriber.py`)
  - Uses `faster-whisper` (`base` model, CPU) to transcribe audio
  - Accepts a `float32` NumPy array directly (no disk I/O)
  - Implements silence detection via RMS energy threshold
  - `listen_and_transcribe()` reads from `audio_queue`, collects frames until silence, then transcribes
  - Joins all Whisper segments into a single string

- [x] **KWS Model downloaded** (`model/kws-zipformer/`)
  - Encoder, decoder, joiner, tokens, and keywords file all present locally

---

## ✅ Phase 3 — Voice Output
> Getting JARVIS to speak back to the user.

- [x] **Text-to-Speech Speaker** (`jarvis/component/speaker.py`)
  - Implemented using `pyttsx3` (offline, no internet required)
  - Runs TTS in a separate `multiprocessing.Process` (`speak_worker`) to avoid blocking the audio capture thread
  - Uses a `multiprocessing.Queue` (`speak_queue`) to decouple the caller from the TTS engine
  - Exposes `speak(text)`, `mp_running()`, and `terminate_speaking()` functions
  - `terminate_speaking()` drains the queue and kills the TTS process instantly

---

## 🔲 Phase 3b — Speaker Fixes (In Progress)
> Resolving known issues with the TTS multiprocessing design.

- [ ] Fix `mp_running()` — `Process()` constructor does not accept a `callback` argument; remove it
- [ ] Ensure `mp_running()` is called inside `speak()` so the process auto-starts
- [ ] Test that `terminate_speaking()` correctly allows a fresh process on next `speak()` call

---

## ✅ Phase 4 — Basic Orchestration
> Wiring the voice pipeline into a single loop.

- [x] **Audio Orchestrator** (`jarvis/orchestrator/audio_orchestrator.py`)
  - Reads audio config from `config/sounddevice.config`
  - Starts the mic stream once (`start_audio_stream`)
  - Main loop: wait for wake word (`kws()`) → flush queue → `listen_and_transcribe()` → print transcript
  - Calls `speak("How can I help you")` after wake word detection
  - Handles graceful shutdown on `KeyboardInterrupt`

- [x] **Main Entry Point** (`main.py`)
  - Imports and calls `run()` from `jarvis.orchestrator.audio_orchestrator`

---

## 🔲 Phase 5 — Brain / Intelligence
> Connecting JARVIS to an LLM for reasoning and conversation.

- [ ] **LLM Integration** (`jarvis/brain/llm.py`) — file exists, currently empty
  - Connect to a language model (local or API-based)
  - Send transcribed user input and receive a response

- [ ] **Memory System** (`jarvis/brain/memory.py`) — file exists, currently empty
  - Implement short-term conversation history (context window)
  - Consider long-term memory storage for user preferences

- [ ] **Response Handler** (`jarvis/brain/response.py`) — file exists, currently empty
  - Post-process LLM output before passing to `speak()`

---

## 🔲 Phase 6 — Full Orchestration Loop
> Connecting transcription → brain → speaker in `audio_orchestrator.py`.

- [ ] Wire `listen_and_transcribe()` output into `llm.py`
- [ ] Pass LLM response through `response.py` and into `speak()`
- [ ] Handle edge cases: empty transcript, LLM errors, TTS process not alive

---

## 🔲 Phase 7 — Skills
> Adding specific capabilities JARVIS can perform.

- [ ] Design a skill system / plugin architecture (`jarvis/skills/`)
- [ ] Implement starter skills (e.g., time/date, open apps, web search)
- [ ] Connect skills to the orchestrator via intent detection
- [ ] `jarvis/skills/example1_skill1.py` exists as a placeholder

---

## 🔲 Phase 8 — Integrations & Interface
> Connecting JARVIS to external services and adding a UI.

- [ ] External API integrations (`integrations/`)
  - HTTP calls via `httpx`
  - Examples: weather, news, calendar

- [ ] User interface (`interface/`)
  - Optional visual interface (GUI or web dashboard)

---

## 🔲 Phase 9 — Testing & Quality
> Making sure everything works reliably.

- [ ] Write unit tests (`tests/unit/`)
- [ ] Write integration tests (`tests/integration/`)
- [ ] Add test audio samples (stub `.wav` files already present in `tests/`)
- [ ] Set up CI/CD or a test runner script

---

## Notes
- The project has been restructured from `modules/` into the `jarvis/` Python package.
- `integrations/` and `interface/` directories are created but intentionally left empty until later phases.
- The KWS model files are stored under `model/kws-zipformer/` (not `sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/` as originally planned).
- `jarvis/brain/` has stub files (`llm.py`, `memory.py`, `response.py`) — all currently empty.
- Libraries previously considered but replaced: `vosk`, `SpeechRecognition`, `python-decouple`, `requests` — see `docs/guide.md` for details.
