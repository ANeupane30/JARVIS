# JARVIS — Library & Tool Reference

This document explains every third-party library and standard library module used in the project,
along with the rationale for choosing them over alternatives.

---

## Tools and Purpose

1. [sherpa-onnx](https://pypi.org/project/sherpa-onnx/): Offline wake-word / keyword spotting detection.
2. [sounddevice](https://pypi.org/project/sounddevice/): Microphone access and real-time raw audio streaming.
3. [faster-whisper](https://pypi.org/project/faster-whisper/): Offline speech-to-text using a quantized Whisper model.
4. [pyttsx3](https://pypi.org/project/pyttsx3/): Offline text-to-speech output.
5. [requests](https://pypi.org/project/requests/): HTTP requests to the OpenRouter LLM API.
6. [python-decouple](https://pypi.org/project/python-decouple/): Loading environment variables from `.env`.
7. [mcp](https://pypi.org/project/mcp/): Model Context Protocol — tool-calling infrastructure for LLM integrations.
8. [pydantic / pydantic-settings](https://pypi.org/project/pydantic/): Data validation and settings management.
9. [httpx](https://pypi.org/project/httpx/): Async-capable HTTP client (planned for integrations).
10. [rich](https://pypi.org/project/rich/): Rich terminal output (planned for CLI improvements).
11. [uvicorn](https://pypi.org/project/uvicorn/) / [starlette](https://pypi.org/project/starlette/): ASGI server and framework (planned for web interface).
12. [typer](https://pypi.org/project/typer/): CLI interface builder (planned for command-line usage).

---

## More About Tools in Detail

### 1. `sherpa-onnx`
A lightweight, fully offline speech toolkit built on ONNX Runtime. We use it specifically for its
**KeywordSpotter** feature, which runs a Zipformer-based model trained on GigaSpeech to detect
wake words (e.g., "Hey JARVIS") in real-time audio streams without any internet connection.

The model files (encoder, decoder, joiner, tokens, keywords) are stored locally under `model/kws-zipformer/`.

**Used in:** `jarvis/component/wakeup.py`
**Config:** `config/sherpa_onnx.config`
**Docs:** [official document](https://k2-fsa.github.io/sherpa/onnx/index.html)

---

### 2. `sounddevice`
A Python binding for the PortAudio library that provides real-time audio input and output.
We use `sd.InputStream` to open a background microphone stream that continuously captures
30ms audio chunks (at 16kHz, mono, float32) and pushes them into a `queue.Queue` for
downstream processing.

**Used in:** `jarvis/component/listener.py`
**Config:** `config/sounddevice.config` (`[kws_audio]` section)
**Docs:** [official document](https://python-sounddevice.readthedocs.io/en/0.5.1/)

---

### 3. `faster-whisper`
A reimplementation of OpenAI's Whisper speech-to-text model using CTranslate2 for faster CPU
inference. We use the `base` model to transcribe captured audio (as a `float32` NumPy array)
into text after the wake word is detected. It runs entirely offline.

Key improvement over the original plan: the transcriber now accepts a NumPy array directly
(no `io.BytesIO` wrapping needed) and joins all output segments into a single string.
The `WhisperModel` is loaded once at module level (not per-call) to avoid slow re-initialization.

**Used in:** `jarvis/component/transcriber.py`
**Docs:** [official document](https://github.com/SYSTRAN/faster-whisper)

---

### 4. `pyttsx3`
A cross-platform text-to-speech library with fully offline conversion support. Allows control
over speech rate and voice selection. JARVIS uses it to speak responses back to the user.

Because `pyttsx3`'s `runAndWait()` is a blocking call, the speaker runs in a separate
`multiprocessing.Process` (`speak_worker`) with a `multiprocessing.Queue` to decouple the
main orchestrator loop from the TTS engine.

**Known issue fixed:** On Windows, SAPI5 COM's `SpVoice` object goes stale after the first
`runAndWait()`. The fix is to call `pyttsx3.init()` fresh inside every loop iteration of
`speak_worker`, giving each utterance a clean COM object at the cost of ~150ms per call.

**Used in:** `jarvis/component/speaker.py`
**Docs:** [official document](https://pyttsx3.readthedocs.io/en/latest/index.html)

---

### 5. `requests`
The standard Python HTTP client library. Used to send transcribed text to the OpenRouter API
and receive LLM responses synchronously. Chosen here over `httpx` because the LLM call is
intentionally synchronous (JARVIS blocks while waiting for the response before speaking).

**Used in:** `jarvis/brain/llm.py`
**Docs:** [official document](https://requests.readthedocs.io/)

---

### 6. `python-decouple`
Loads environment variables from the `.env` file cleanly with type coercion. Used to read
`OPENROUTER_API_KEY` without importing the full `python-dotenv` stack.

**Used in:** `jarvis/brain/llm.py`
**Docs:** [official document](https://github.com/HBNetwork/python-decouple)

---

### 7. `mcp`
The official Python SDK for the **Model Context Protocol** — a standardised interface for
connecting LLMs to external tools (functions, APIs, databases). JARVIS implements both sides:

- **Server side** (`mcp_server/server.py`): exposes tools (e.g., `get_weather`) that the LLM can call
- **Client side** (`jarvis/brain/mcp_client.py`): connects to the server, lists available tools, and dispatches tool calls synchronously

The MCP library uses `asyncio` internally. The `MCPClient` bridges this by running a private
asyncio event loop on a daemon background thread, exposing a clean synchronous API to the rest
of JARVIS (which is not async).

**Used in:** `jarvis/brain/mcp_client.py`, `mcp_server/server.py`
**Docs:** [official document](https://modelcontextprotocol.io/)

---

### 8. `pydantic` / `pydantic-settings`
Data validation library used by the `mcp` library internally, and available for defining
typed configuration models in future JARVIS settings management.

**Current use:** Pulled in as a dependency of `mcp`; planned for structured config management.
**Docs:** [official document](https://docs.pydantic.dev/)

---

### 9. `httpx`
A modern, fully featured HTTP client for Python. Supports both synchronous and asynchronous
requests out of the box. Planned for use in `integrations/` for non-blocking API calls
(e.g., weather, news, calendar) that should not stall the main orchestrator loop.

**Planned use in:** `integrations/`
**Docs:** [official document](https://www.python-httpx.org/)

---

### 10. `rich`
A terminal formatting library for beautiful output — colours, tables, progress bars, panels.
Planned for improving the developer-facing console output of JARVIS during operation.

**Planned use in:** Logging and diagnostic output improvements.
**Docs:** [official document](https://rich.readthedocs.io/)

---

### 11. `uvicorn` / `starlette`
An ASGI web server (`uvicorn`) and lightweight web framework (`starlette`). Included for a
future optional web dashboard or REST control interface for JARVIS.

**Planned use in:** `interface/`
**Docs:** [uvicorn](https://www.uvicorn.org/) | [starlette](https://www.starlette.io/)

---

### 12. `typer`
A CLI framework built on top of Python type hints. Planned for adding command-line flags
to `main.py` (e.g., `--test`, `--model`, `--verbose`) without manually parsing `sys.argv`.

**Planned use in:** `main.py` / CLI entry point
**Docs:** [official document](https://typer.tiangolo.com/)

---

## Standard Library Modules Used

These are built-in Python modules — no installation required.

| Module | Used In | Purpose |
|---|---|---|
| `configparser` | `wakeup.py`, `audio_orchestrator.py` | Read `.config` files (INI format) for model paths, sample rates, and audio settings |
| `queue` | `listener.py`, `wakeup.py`, `transcriber.py` | Thread-safe `Queue` that bridges the background audio capture thread with the KWS and transcription loops |
| `numpy` | `transcriber.py` | Array concatenation, RMS energy calculation for silence detection, dtype conversion |
| `multiprocessing` | `speaker.py` | `Process`, `Queue`, and `Event` for non-blocking TTS — avoids blocking the audio stream while JARVIS is speaking |
| `asyncio` | `mcp_client.py`, `mcp_server/server.py` | Async event loop for MCP protocol; client runs a private loop on a background thread |
| `threading` | `mcp_client.py` | Background thread hosting the asyncio loop to bridge async MCP with synchronous JARVIS code |
| `pathlib` | `main.py`, `mcp_client.py` | Cross-platform path construction for model files and server paths |
| `os` | `main.py` | DLL directory registration on Windows to fix `onnxruntime` vs `sherpa_onnx` loading order |

---

## Previously Considered Tools (Not Currently In Use)

These libraries were explored during early planning but were replaced or deferred.

| Library | Reason Not Used |
|---|---|
| [vosk](https://pypi.org/project/vosk/) | Replaced by `faster-whisper`, which offers better accuracy on the same hardware |
| [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) | Replaced by `sounddevice` for direct mic access and `faster-whisper` for STT |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Replaced by `python-decouple` which provides the same `.env` loading with cleaner type handling |
| [io](https://docs.python.org/3/library/io.html) | Previously used to wrap raw audio bytes in `BytesIO`; no longer needed since `faster-whisper` accepts NumPy arrays directly |