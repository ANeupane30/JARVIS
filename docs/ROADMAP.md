# JARVIS — Project Roadmap

A personal AI voice assistant inspired by Iron Man's JARVIS.
This roadmap tracks what has been completed, what is in progress, and what is planned next.

---

## ✅ Phase 1 — Project Foundation
> Setting up the project structure, environment, and tooling.

- [x] Initialize Git repository
- [x] Set up Python virtual environment (`.venv`) using `uv`
- [x] Create `pyproject.toml` with all dependencies (migrated from `requirements.txt`)
- [x] Set up `.env` and `.env.example` for environment variables (`BOT_NAME`, `USER_NAME`, `OPENROUTER_API_KEY`)
- [x] Create folder structure (`jarvis/`, `jarvis/component/`, `jarvis/orchestrator/`, `jarvis/brain/`, `jarvis/skills/`, `config/`, `model/`, `docs/`, `tests/`, `scripts/`, `integrations/`, `interface/`, `mcp_server/`)
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
  - Runs TTS in a dedicated `multiprocessing.Process` (`speak_worker`) to avoid blocking the audio capture thread
  - Uses a `multiprocessing.Queue` (`speak_queue`) and `multiprocessing.Event` (`stop_event`) for inter-process communication
  - `speak_worker()` re-initialises the `pyttsx3` engine on each utterance to work around the Windows SAPI5 COM stale-state bug
  - `prewarm()` starts the subprocess at app launch so the first utterance has no cold-start delay
  - `speak(text)` enqueues text non-blocking; `terminate_speaking()` drains the queue and aborts mid-sentence via the `stop_event`

---

## ✅ Phase 3b — Speaker Fixes
> Resolved known issues with the TTS multiprocessing design.

- [x] Root cause identified: SAPI5 COM SpVoice object goes stale after first `runAndWait()` — subsequent calls produce no audio
- [x] Fix: re-initialise `pyttsx3.init()` on every utterance inside `speak_worker()` (costs ~150ms, avoids silent audio bug)
- [x] `prewarm()` added: starts the subprocess at app launch, hiding cold-start latency behind KWS model load time
- [x] `terminate_speaking()` sets `stop_event` to abort mid-sentence via `on_word` callback; process is kept alive to avoid 5s reload cost

---

## ✅ Phase 4 — Basic Orchestration
> Wiring the voice pipeline into a single loop.

- [x] **Audio Orchestrator** (`jarvis/orchestrator/audio_orchestrator.py`)
  - Reads audio config from `config/sounddevice.config`
  - Starts the mic stream once (`start_audio_stream`) — stream never restarted between KWS and STT
  - Calls `prewarm()` at startup so TTS subprocess is ready before the first wake word
  - Main loop: wait for wake word (`kws()`) → flush `audio_queue` (discard wake-word audio) → `speak("How can I help you")` → `listen_and_transcribe()` → send to LLM → speak response
  - Handles graceful shutdown on `KeyboardInterrupt` with `finally: stream.stop() + stream.close()`

- [x] **Diagnostic Orchestrator** (`jarvis/orchestrator/test_orchestrator.py`)
  - Drop-in replacement for `audio_orchestrator.py` used during debugging
  - Logs timestamps, cycle numbers, TTS process state, and `audio_queue` depth at every step
  - Helper functions: `log()`, `tts_state()`, `audio_state()`, `divider()`
  - Calls `terminate_speaking()` before each greeting to handle mid-speech interrupts

- [x] **Main Entry Point** (`main.py`)
  - Windows DLL path fix for `onnxruntime` / `sherpa_onnx` loaded before imports
  - Imports and calls `run()` from `jarvis.orchestrator.audio_orchestrator`

---

## ✅ Phase 5 — Brain / Intelligence
> Connecting JARVIS to an LLM for reasoning and conversation.

- [x] **LLM Integration** (`jarvis/brain/llm.py`)
  - Connects to OpenRouter API (`https://openrouter.ai/api/v1/responses`)
  - Uses `openai/o4-mini` model with up to 9,000 output tokens
  - `llm_response(text)` sends transcript and returns raw JSON response dict
  - API key loaded from `.env` via `python-decouple`

- [x] **Response Formatter** (`jarvis/component/response_formatter.py`)
  - `complete_json_response(data)` parses OpenRouter response JSON
  - Extracts the first text message from `output[].content[].text`

- [ ] **Memory System** (`jarvis/brain/memory.py`) — file exists, currently empty
  - Implement short-term conversation history (context window)
  - Consider long-term memory storage for user preferences

- [ ] **Response Handler** (`jarvis/brain/response.py`) — file exists, currently empty
  - Post-process LLM output before passing to `speak()` (cleaning, chunking for TTS)

---

## ✅ Phase 6 — Full Orchestration Loop
> Connecting transcription → brain → speaker in `audio_orchestrator.py`.

- [x] Wire `listen_and_transcribe()` output into `llm_response()` from `llm.py`
- [x] Parse LLM JSON response via `complete_json_response()` from `response_formatter.py`
- [x] Pass parsed LLM response text into `speak()`
- [x] Basic edge case handling: empty transcript returns to KWS loop without LLM call

---

## ✅ Phase 6b — MCP (Model Context Protocol) Infrastructure
> Giving JARVIS the ability to call external tools via a standardised protocol.

- [x] **MCP Server** (`mcp_server/server.py`)
  - Implements the MCP server protocol using the low-level `mcp` library
  - Runs as a subprocess communicating via stdio
  - Exposes a `get_weather` tool (stub returning fake data — real integration planned)
  - Server name: `jarvis-server`, version `0.1.0`

- [x] **MCP Client** (`jarvis/brain/mcp_client.py`)
  - `MCPClient` class bridges async MCP protocol to synchronous JARVIS code
  - Spins up a dedicated background asyncio event loop on a daemon thread
  - `connect()` — starts the MCP server subprocess and initialises the session
  - `get_tools()` — returns available tools in Anthropic API format (`name`, `description`, `input_schema`)
  - `call_tool(name, arguments)` — synchronously dispatches a tool call and returns the text result
  - Module-level singleton `mcp_client = MCPClient()` for easy reuse

---

## 🔲 Phase 7 — Skills
> Adding specific capabilities JARVIS can perform.

- [ ] Design a skill system / plugin architecture (`jarvis/skills/`)
- [ ] Implement starter skills (e.g., time/date, open apps, web search)
- [ ] Connect skills to the orchestrator via intent detection or LLM tool calling
- [ ] Wire MCP tool results into the LLM context (tool-use loop)
- [ ] Implement real `get_weather` tool in `mcp_server/server.py` (replace stub)
- [ ] `jarvis/skills/example1_skill1.py` exists as a placeholder

---

## 🔲 Phase 8 — Memory & Context
> Making JARVIS remember conversations.

- [ ] Implement `jarvis/brain/memory.py` — short-term conversation history (rolling context window)
- [ ] Implement `jarvis/brain/response.py` — response cleanup (strip markdown, handle long responses)
- [ ] Pass conversation history into LLM calls for multi-turn dialogue
- [ ] Optional: long-term memory storage (user preferences, facts)

---

## 🔲 Phase 9 — Integrations & Interface
> Connecting JARVIS to external services and adding a UI.

- [ ] External API integrations (`integrations/`)
  - HTTP calls via `httpx`
  - Examples: weather, news, calendar

- [ ] User interface (`interface/`)
  - Optional visual interface (GUI or web dashboard)
  - Potential: FastAPI/Starlette web server (`uvicorn` already a dependency)

---

## 🔲 Phase 10 — Testing & Quality
> Making sure everything works reliably.

- [ ] Write unit tests (`tests/unit/`)
- [ ] Write integration tests (`tests/integration/`)
- [ ] Add test audio samples (stub `.wav` files already present in `tests/`)
- [ ] Set up CI/CD or a test runner script

---

## Notes
- Project uses `uv` for dependency management (`pyproject.toml` + `uv.lock`), not `pip`/`requirements.txt`.
- `integrations/` and `interface/` directories are created but intentionally left empty until later phases.
- The KWS model files are stored under `model/kws-zipformer/`.
- `jarvis/brain/memory.py` and `jarvis/brain/response.py` are still empty stubs.
- MCP infrastructure (`mcp_client.py`, `mcp_server/server.py`) is implemented but not yet wired into the LLM tool-use loop.
- Windows DLL loading order fix in `main.py` ensures the venv's `onnxruntime` is loaded before `sherpa_onnx` can pull the System32 DLL.
