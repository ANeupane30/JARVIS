# JARVIS — Library & Tool Reference

This document explains every third-party library and standard library module used in the project,
along with the rationale for choosing them over alternatives.

---

## Tools and Purpose

1. [sherpa-onnx](https://pypi.org/project/sherpa-onnx/): Offline wake-word / keyword spotting detection.
2. [sounddevice](https://pypi.org/project/sounddevice/): Microphone access and real-time raw audio streaming.
3. [faster-whisper](https://pypi.org/project/faster-whisper/): Offline speech-to-text using a quantized Whisper model.
4. [pyttsx3](https://pypi.org/project/pyttsx3/): Offline text-to-speech output.
5. [httpx](https://pypi.org/project/httpx/): HTTP requests to external APIs (future integrations).

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

**Used in:** `jarvis/component/speaker.py`
**Docs:** [official document](https://pyttsx3.readthedocs.io/en/latest/index.html)

---

### 5. `httpx`
A modern, fully featured HTTP client for Python. Used in place of the older `requests` library
because it supports both synchronous and asynchronous requests out of the box, which will be
important for making non-blocking API calls within JARVIS skills.

**Planned use in:** `integrations/`
**Docs:** [official document](https://www.python-httpx.org/)

---

## Standard Library Modules Used

These are built-in Python modules — no installation required.

| Module | Used In | Purpose |
|---|---|---|
| `configparser` | `wakeup.py`, `audio_orchestrator.py` | Read `.config` files (INI format) for model paths, sample rates, and audio settings |
| `queue` | `listener.py`, `wakeup.py`, `transcriber.py` | Thread-safe `Queue` that bridges the background audio capture thread with the KWS and transcription loops |
| `io` | *(removed from current transcriber)* | Previously used to wrap raw audio bytes in `BytesIO`; no longer needed since `faster-whisper` now accepts NumPy arrays directly |
| `numpy` | `transcriber.py` | Array concatenation, RMS energy calculation for silence detection, dtype conversion |
| `multiprocessing` | `speaker.py` | `Process`, `Queue`, and `Event` for non-blocking TTS — avoids blocking the audio stream while JARVIS is speaking |

---

## Previously Considered Tools (Not Currently In Use)

These libraries were explored during early planning but were replaced or deferred.

| Library | Reason Not Used |
|---|---|
| [vosk](https://pypi.org/project/vosk/) | Replaced by `faster-whisper`, which offers better accuracy on the same hardware |
| [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) | Replaced by `sounddevice` for direct mic access and `faster-whisper` for STT |
| [python-decouple](https://pypi.org/project/python-decouple/) | `.env` file is managed directly; may be added later if configuration complexity grows |
| [requests](https://pypi.org/project/requests/) | Replaced by `httpx` which supports both sync and async HTTP calls |