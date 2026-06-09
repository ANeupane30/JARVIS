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
config.read("config/sounddevice.config")  # read the file

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

---

## `config/sounddevice.config`

Used by: `modules/voice/listener.py`

```ini
[audio]
SAMPLE_RATE = 16000
BLOCK_DURATION = 0.03
CHANNELS = 1
```

| Key | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `16000` | 16,000 audio samples per second (16 kHz). This is the standard for speech recognition models — both sherpa-onnx and faster-whisper were trained on 16kHz audio. If you change this, the models will not work correctly. |
| `BLOCK_DURATION` | `0.03` | Each audio chunk is 30 milliseconds long. At 16kHz, this means each chunk = 16000 × 0.03 = **480 samples**. Smaller blocks = lower latency. Larger blocks = less CPU overhead. 30ms is a standard choice for real-time KWS. |
| `CHANNELS` | `1` | Mono audio (1 channel). Stereo (2 channels) is not needed for speech recognition and would double the data size. |

---

## `config/sherpa_onnx.config`

Used by: `modules/voice/wakeup.py`

```ini
[kws]
SAMPLE_RATE = 16000
MODEL_DIR = sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01
TOKEN = sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/tokens.txt
ENCODER = sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/encoder-epoch-12-avg-2-chunk-16-left-64.onnx
DECODER = sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/decoder-epoch-12-avg-2-chunk-16-left-64.onnx
JOINER = sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/joiner-epoch-12-avg-2-chunk-16-left-64.onnx
KEYWORDS_FILE = sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/keywords.txt
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
| `MODEL_DIR` | Root folder of all model files (used for reference, not directly read by code) |
| `TOKEN` | Path to `tokens.txt` — a vocabulary file mapping integers to characters (e.g., 42 → "h") |
| `ENCODER` | Path to the encoder ONNX model — converts raw audio features into a high-level representation |
| `DECODER` | Path to the decoder ONNX model — predicts the next character/token given encoder outputs |
| `JOINER` | Path to the joiner ONNX model — combines encoder and decoder outputs to produce the final prediction |

All three (encoder, decoder, joiner) are required. Together they form the full Zipformer
transducer model. The filename `epoch-12-avg-2-chunk-16-left-64` tells you:
- Trained for 12 epochs, averaged over 2 checkpoints
- Chunk size of 16 frames (streaming chunk)
- Left context of 64 frames

### Detection Tuning Parameters

| Key | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `16000` | Must match the audio capture rate — same as sounddevice.config |
| `KEYWORD_SCORE` | `1.0` | A score multiplier applied to keyword tokens during decoding. Higher values make the model more likely to detect the keyword (more sensitive). Lower = harder to trigger (fewer false positives). |
| `KEYWORD_THRESHOLD` | `0.25` | The minimum confidence required to confirm a detection. Range is 0.0–1.0. `0.25` means 25% confidence is enough. Lower = more sensitive (more false positives). Higher = stricter (might miss quiet speech). |
| `NUM_TRAILING_BLANKS` | `8` | The number of consecutive silence/blank frames that must follow the keyword before it is confirmed. This prevents partial word matches. 8 frames × 30ms = 240ms of silence required after the keyword. |
| `PROVIDER` | `cpu` | Which hardware to run inference on. `cpu` uses ONNX Runtime on CPU. Could be `cuda` for NVIDIA GPU or `coreml` for Apple Silicon. |
| `NUM_THREADS` | `1` | Number of CPU threads for the ONNX model. 1 is fine for a 3.3M model. Increase if inference is slow. |
| `MAX_ACTIVE_PATHS` | `4` | Beam size for beam search — how many candidate transcriptions the decoder tracks at once. 4 is a good balance between accuracy and speed. |

---

## `.env` and `.env.example`

Not read by `configparser` — these are environment variables read at runtime.

**`.env.example`** (template, safe to commit):
```
BOT_NAME=JARVIS
USER_NAME=Enter_Your_Name
```

**`.env`** (your real values, never committed to git):
```
BOT_NAME=JARVIS
USER_NAME=Aseem
```

These will be used by the brain/orchestrator modules once they are implemented —
for example, so JARVIS can address you by name in responses.

---

## How to Tune the Wake Word Detection

If JARVIS triggers too often (false positives):
- Increase `KEYWORD_THRESHOLD` (e.g., `0.4` or `0.5`)
- Increase `NUM_TRAILING_BLANKS` (e.g., `12`)
- Decrease `KEYWORD_SCORE` (e.g., `0.8`)

If JARVIS misses the wake word (false negatives):
- Decrease `KEYWORD_THRESHOLD` (e.g., `0.15`)
- Increase `KEYWORD_SCORE` (e.g., `1.5`)
- Decrease `NUM_TRAILING_BLANKS` (e.g., `4`)

No code changes needed — just edit the values in `config/sherpa_onnx.config`.
