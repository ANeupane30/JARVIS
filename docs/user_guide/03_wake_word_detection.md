# 03 — Wake Word Detection

**File:** `jarvis/component/wakeup.py`
**Status:** ✅ Working
**Library:** `sherpa-onnx`
**Depends on:** `listener.py` (imports `audio_queue`)

---

## What This File Does

This file listens to the audio stream from `listener.py` and **detects when you say
the wake word** (e.g., "Hey JARVIS"). When the wake word is detected, it returns `True`
to the caller (the orchestrator), which then flushes the queue and starts transcription.

It is no longer a standalone script — it is invoked by `audio_orchestrator.py` in a loop.

---

## How It Works — Step by Step

### Step 1: Load Config (Module Level)
```python
config = configparser.ConfigParser()
config.read("config/sherpa_onnx.config")  # KWS model settings
config.read("config/sounddevice.config")  # audio settings (sample rate etc.)

sample_rate        = int(config['kws_audio']['SAMPLE_RATE'])
block_duration     = float(config['kws_audio']['BLOCK_DURATION'])
channels           = int(config['kws_audio']['CHANNELS'])

tokens             = str(config['kws']['TOKEN'])
encoder            = str(config['kws']['ENCODER'])
decoder            = str(config['kws']['DECODER'])
joiner             = str(config['kws']['JOINER'])
num_threads        = int(config['kws']['NUM_THREADS'])
max_active_paths   = int(config['kws']['MAX_ACTIVE_PATHS'])
keywords_file      = str(config['kws']['KEYWORDS_FILE'])
keywords_score     = float(config['kws']['KEYWORD_SCORE'])
keywords_threshold = float(config['kws']['KEYWORD_THRESHOLD'])
num_trailing_blanks= int(config['kws']['NUM_TRAILING_BLANKS'])
provider           = str(config['kws']['PROVIDER'])
```

> **Note:** Audio config comes from the `[kws_audio]` section of `sounddevice.config`
> (not `[audio]`). Both config files are read at module import time, not inside the function.

---

### Step 2: Create the KeywordSpotter (Module Level)
```python
keyword_spotter = sherpa_onnx.KeywordSpotter(
    tokens=tokens,
    encoder=encoder,
    decoder=decoder,
    joiner=joiner,
    num_threads=num_threads,
    max_active_paths=max_active_paths,
    keywords_file=keywords_file,
    keywords_score=keywords_score,
    keywords_threshold=keywords_threshold,
    num_trailing_blanks=num_trailing_blanks,
    provider=provider,
)
```
This loads the Zipformer ONNX model into memory **once** at module import time.
The model is a neural network trained to spot specific words in a continuous audio stream.

**What is a Zipformer?** A Transformer-based acoustic model optimised for
streaming (chunk-by-chunk) speech recognition. "3.3M" = 3.3 million parameters —
small enough to run fast on CPU.

**What is GigaSpeech?** The training dataset — 10,000 hours of English audio from
podcasts, YouTube, audiobooks.

---

### Step 3: The `kws()` Function
```python
def kws():
    kws_stream = keyword_spotter.create_stream()
    print("KWS_Stream is on")

    while True:
        try:
            samples = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        samples = samples.reshape(-1)
        kws_stream.accept_waveform(sample_rate, samples)

        while keyword_spotter.is_ready(kws_stream):
            keyword_spotter.decode_stream(kws_stream)

        result = keyword_spotter.get_result(kws_stream)
        if result:
            return True
```

Each call to `kws()`:
1. Creates a fresh KWS stream (stateful context for one listening session)
2. Continuously reads audio chunks from `audio_queue`
3. Feeds each chunk into the stream and decodes
4. Returns `True` the moment a keyword is detected

The orchestrator calls `kws()` in a loop — a new stream is implicitly created each call,
so the context is always clean after detection.

#### Why `reshape(-1)`?
`sounddevice` gives audio as a 2D NumPy array: shape `(480, 1)` for mono audio.
`sherpa-onnx` expects a 1D array: shape `(480,)`.
`.reshape(-1)` flattens any shape into 1D.

#### Why `is_ready()` before `decode_stream()`?
The Zipformer model processes audio in **chunks** (streaming model). `is_ready()`
checks whether the model has received enough audio to make a reliable decision for the
next chunk. You must keep calling `decode_stream()` until `is_ready()` returns False.

#### Why `timeout=0.1` on `queue.get()`?
Prevents the loop from blocking forever if no audio arrives.
The `except queue.Empty: continue` means we simply try again — not an error.

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Model loaded at module level | Avoids reloading the model on every call (would be very slow) |
| `kws()` creates a new stream on each call | Ensures clean model state for every new listening session |
| Returns `True` on detection | Simple signal to the orchestrator — no complex return value needed |
| `provider="cpu"` | Runs inference on CPU using ONNX Runtime — no GPU required |

---

## Configuration Reference (`config/sherpa_onnx.config`)

| Key | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `16000` | Audio must be 16kHz — what the model was trained on |
| `TOKEN` | `model/kws-zipformer/tokens.txt` | Maps model output integers back to characters |
| `ENCODER` | `model/kws-zipformer/encoder-...onnx` | The encoder half of the Zipformer model |
| `DECODER` | `model/kws-zipformer/decoder-...onnx` | The decoder half of the Zipformer model |
| `JOINER` | `model/kws-zipformer/joiner-...onnx` | Combines encoder + decoder outputs |
| `KEYWORDS_FILE` | `model/kws-zipformer/keywords.txt` | Text file listing wake words to detect |
| `KEYWORD_SCORE` | `1.0` | Boost factor for keyword tokens (higher = easier to trigger) |
| `KEYWORD_THRESHOLD` | `0.25` | Minimum confidence score to count as a detection |
| `NUM_THREADS` | `1` | Number of CPU threads for inference |
| `MAX_ACTIVE_PATHS` | `4` | Beam width for beam search decoding |
| `NUM_TRAILING_BLANKS` | `8` | Silence frames required after keyword before confirmation |
| `PROVIDER` | `cpu` | ONNX Runtime execution provider |

See [`05_configuration.md`](05_configuration.md) for tuning guidance.
