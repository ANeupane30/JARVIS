# 05 — Configuration Files

This document explains every configuration file in the `config/` folder — what each
setting does and why it has the value it has.

Configuration is stored in **INI-format** `.config` files and read using Python's
built-in `configparser` module. This keeps settings separate from source code.

---

## How configparser Works

```python
import configparser

config = configparser.ConfigParser()
config.read("config/sounddevice.config")   # read the file

value = config['section_name']['KEY_NAME']  # access a value
```

INI format looks like:
```ini
[section_name]
KEY_NAME = value
ANOTHER_KEY = another_value
```

All values are read as **strings** by default. The code manually converts them:
- `int(config['kws']['NUM_THREADS'])` → integer
- `float(config['kws']['KEYWORD_SCORE'])` → float
- `str(config['kws']['TOKEN'])` → string (explicit, for clarity)

> **Multiple files can be read by the same `ConfigParser` instance.** In `wakeup.py`,
> both `sherpa_onnx.config` and `sounddevice.config` are read into the same `config`
> object, so all sections from both files are accessible.

---

## `config/sounddevice.config`

Used by: `jarvis/component/listener.py` (indirectly), `jarvis/orchestrator/audio_orchestrator.py`, `jarvis/component/wakeup.py`

```ini
[kws_audio]
SAMPLE_RATE = 16000
BLOCK_DURATION = 0.03
CHANNELS = 1
```

> **Note:** The section is `[kws_audio]`, not `[audio]`. All code that reads this file
> accesses `config['kws_audio']`.

| Key | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `16000` | 16,000 audio samples per second (16 kHz). Both sherpa-onnx and faster-whisper were trained on 16kHz audio. Changing this will break the models. |
| `BLOCK_DURATION` | `0.03` | Each audio chunk is 30 milliseconds. At 16kHz: 16000 × 0.03 = **480 samples** per chunk. Smaller = lower latency. Larger = less CPU overhead. 30ms is standard for real-time KWS. |
| `CHANNELS` | `1` | Mono audio (1 channel). Stereo is unnecessary for speech recognition and doubles data size. |

---

## `config/sherpa_onnx.config`

Used by: `jarvis/component/wakeup.py`

```ini
[kws]
SAMPLE_RATE = 16000
MODEL_DIR = model\kws-zipformer
TOKEN = model/kws-zipformer/tokens.txt
ENCODER = model/kws-zipformer/encoder-epoch-12-avg-2-chunk-16-left-64.onnx
DECODER = model/kws-zipformer/decoder-epoch-12-avg-2-chunk-16-left-64.onnx
JOINER = model/kws-zipformer/joiner-epoch-12-avg-2-chunk-16-left-64.onnx
KEYWORDS_FILE = model/kws-zipformer/keywords.txt
KEYWORD_SCORE = 1.0
KEYWORD_THRESHOLD = 0.25
PROVIDER = cpu
NUM_THREADS = 1
MAX_ACTIVE_PATHS = 4
NUM_TRAILING_BLANKS = 8
```

### Model File Paths

| Key | Meaning |
|---|---|
| `MODEL_DIR` | Root folder of all model files (reference only — not read directly by code) |
| `TOKEN` | Path to `tokens.txt` — vocabulary file mapping integers to characters (e.g., 42 → "h") |
| `ENCODER` | Path to the encoder ONNX model — converts raw audio features into high-level representations |
| `DECODER` | Path to the decoder ONNX model — predicts the next character/token given encoder outputs |
| `JOINER` | Path to the joiner ONNX model — combines encoder and decoder outputs for final prediction |
| `KEYWORDS_FILE` | Path to `keywords.txt` — one wake word or phrase per line |

All three (encoder, decoder, joiner) are required. Together they form the Zipformer
transducer model. The filename `epoch-12-avg-2-chunk-16-left-64` tells you:
- Trained for 12 epochs, averaged over 2 checkpoints
- Chunk size of 16 frames (streaming chunk)
- Left context of 64 frames

> **Path format note:** `MODEL_DIR` uses a backslash (`model\kws-zipformer`) for Windows
> display purposes only. The actual file path keys use forward slashes, which work on
> both Windows and Linux in Python's `open()` and ONNX Runtime.

### Detection Tuning Parameters

| Key | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `16000` | Must match the audio capture rate in `sounddevice.config` |
| `KEYWORD_SCORE` | `1.0` | Score multiplier applied to keyword tokens during decoding. Higher = more sensitive (more false positives). |
| `KEYWORD_THRESHOLD` | `0.25` | Minimum confidence to confirm a detection. Range 0.0–1.0. `0.25` = 25% confidence needed. |
| `NUM_TRAILING_BLANKS` | `8` | Consecutive silence frames required after the keyword. 8 × 30ms = **240ms** of silence required. Prevents partial word matches. |
| `PROVIDER` | `cpu` | ONNX Runtime execution provider. `cpu` uses CPU. Could be `cuda` (NVIDIA) or `coreml` (Apple Silicon). |
| `NUM_THREADS` | `1` | CPU threads for the ONNX model. 1 is fine for a 3.3M model. Increase if inference is slow. |
| `MAX_ACTIVE_PATHS` | `4` | Beam size — how many candidate transcriptions the decoder tracks at once. 4 balances accuracy and speed. |

---

## `.env` and `.env.example`

Not read by `configparser` — these are environment variables loaded at runtime.

**`.env.example`** (template, safe to commit):
```
BOT_NAME=JARVIS <-- Change this if you prefer to call your AI by another name
USER_NAME=Enter_Your_Name
```

**`.env`** (your real values, never committed to git):
```
BOT_NAME=JARVIS
USER_NAME=Aseem
```

These will be used by the brain/orchestrator modules once implemented —
for example, so JARVIS can address you by name in responses.

---

## How to Tune Wake Word Detection

**JARVIS triggers too often (false positives):**
```ini
KEYWORD_THRESHOLD = 0.4       ; increase from 0.25 (stricter)
NUM_TRAILING_BLANKS = 12      ; increase from 8 (more silence required)
KEYWORD_SCORE = 0.8           ; decrease from 1.0 (less boost)
```

**JARVIS misses the wake word (false negatives):**
```ini
KEYWORD_THRESHOLD = 0.15      ; decrease from 0.25 (more permissive)
KEYWORD_SCORE = 1.5           ; increase from 1.0 (more boost)
NUM_TRAILING_BLANKS = 4       ; decrease from 8 (less silence required)
```

No code changes needed — just edit `config/sherpa_onnx.config`.

---

## How to Tune Silence Detection (Transcriber)

The silence detection threshold in `jarvis/component/transcriber.py` is currently hardcoded:

```python
silence_timeout: float = 1.5   # seconds of silence to stop recording
max_duration:    float = 15.0  # maximum recording length
threshold:       float = 0.01  # RMS energy below this = silence
```

To calibrate `threshold`, add a temporary print statement to see actual RMS values
during silence on your microphone:
```python
rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
print(f"RMS: {rms:.6f}")
```

Set `threshold` slightly above your ambient silence RMS.
