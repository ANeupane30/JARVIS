### Tools and Purpose
1. [sherpa-onnx](https://pypi.org/project/sherpa-onnx/): We are using this for offline wake-word / keyword spotting detection.
2. [sounddevice](https://pypi.org/project/sounddevice/): We are using this to access the microphone and stream raw audio data in real time.
3. [faster-whisper](https://pypi.org/project/faster-whisper/): We are using this to convert speech to text offline using a quantized Whisper model.
4. [pyttsx3](https://pypi.org/project/pyttsx3/): We are using this to convert text to speech offline.
5. [httpx](https://pypi.org/project/httpx/): We are using this to make HTTP requests to external APIs.


### More About Tools in Detail
1. [sherpa-onnx](https://pypi.org/project/sherpa-onnx/): A lightweight, fully offline speech toolkit built on ONNX Runtime. We use it specifically for its **KeywordSpotter** feature, which runs a Zipformer-based model trained on GigaSpeech to detect wake words (e.g., "Hey JARVIS") in real-time audio streams without any internet connection. The model files (encoder, decoder, joiner, tokens) are stored locally under the `sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/` directory. For more information check [official document](https://k2-fsa.github.io/sherpa/onnx/index.html)

2. [sounddevice](https://pypi.org/project/sounddevice/): A Python binding for the PortAudio library that provides real-time audio input and output. We use `sd.InputStream` to open a background microphone stream that continuously captures 30ms audio chunks (at 16kHz, mono, float32) and pushes them into a `queue.Queue` for downstream processing. For more information check [official document](https://python-sounddevice.readthedocs.io/en/0.5.1/)

3. [faster-whisper](https://pypi.org/project/faster-whisper/): A re-implementation of OpenAI's Whisper speech-to-text model using CTranslate2 for faster CPU inference. We use the `base` model to transcribe captured audio bytes into text after the wake word is detected. It runs entirely offline with no data sent to external servers. For more information check [official document](https://github.com/SYSTRAN/faster-whisper)

4. [pyttsx3](https://pypi.org/project/pyttsx3/): A cross-platform text-to-speech library with fully offline conversion support. This allows control over speed/rate of speech and volume. Intended for use in `speaker.py` to have JARVIS speak responses back to the user. For more information check [official document](https://pyttsx3.readthedocs.io/en/latest/index.html)

5. [httpx](https://pypi.org/project/httpx/): A modern, fully featured HTTP client for Python. We use this in place of the older `requests` library because it supports both synchronous and asynchronous requests out of the box, which will be important for making non-blocking API calls within JARVIS skills. For more information check [official document](https://www.python-httpx.org/)


### Standard Library Modules Used
These are built-in Python modules — no installation required.

- **configparser**: Used to read `.config` files (e.g., `sherpa_onnx.config`, `sounddevice.config`) that store model paths, sample rates, and audio settings in an INI-style format.
- **queue**: Used to create a thread-safe `Queue` that bridges the background audio capture thread (sounddevice) with the main keyword-spotting loop.
- **io**: Used in `speech_to_text.py` to wrap raw audio bytes in a `BytesIO` buffer so faster-whisper can read them as if they were a file.


### Previously Considered Tools (Not Currently In Use)
These libraries were explored during early planning but were replaced or deferred.

| Library | Reason Not Used |
|---|---|
| [vosk](https://pypi.org/project/vosk/) | Replaced by `faster-whisper`, which offers better accuracy on the same hardware |
| [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) | Replaced by `sounddevice` for direct mic access and `faster-whisper` for STT |
| [python-decouple](https://pypi.org/project/python-decouple/) | `.env` file is managed directly; may be added later if configuration complexity grows |
| [requests](https://pypi.org/project/requests/) | Replaced by `httpx` which supports both sync and async HTTP calls |