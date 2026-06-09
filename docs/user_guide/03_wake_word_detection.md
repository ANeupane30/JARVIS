# 03 — Wake Word Detection

**File:** `modules/voice/wakeup.py`
**Status:** ✅ Working
**Library:** `sherpa-onnx`
**Depends on:** `listener.py`

---

## What This File Does

This file listens to the audio stream from `listener.py` and **detects when you say
the wake word** (e.g., "Hey JARVIS"). When the wake word is detected, it prints a message
and resets itself to listen again.

It is currently a **standalone script** — run it directly, not through `main.py`.

---

## How It Works — Step by Step

### Step 1: Load Config
```python
config = configparser.ConfigParser()
config.read("config/sherpa_onnx.config")

sample_rate       = int(config['kws']['SAMPLE_RATE'])       # 16000
tokens            = str(config['kws']['TOKEN'])              # path to tokens.txt
encoder           = str(config['kws']['ENCODER'])            # path to encoder .onnx
decoder           = str(config['kws']['DECODER'])            # path to decoder .onnx
joiner            = str(config['kws']['JOINER'])             # path to joiner .onnx
num_threads       = int(config['kws']['NUM_THREADS'])        # 1
max_active_paths  = int(config['kws']['MAX_ACTIVE_PATHS'])   # 4
keywords_file     = str(config['kws']['KEYWORDS_FILE'])      # path to keywords.txt
keywords_score    = float(config['kws']['KEYWORD_SCORE'])    # 1.0
keywords_threshold= float(config['kws']['KEYWORD_THRESHOLD'])# 0.25
num_trailing_blanks = int(config['kws']['NUM_TRAILING_BLANKS'])# 8
provider          = str(config['kws']['PROVIDER'])           # "cpu"
```
All model file paths and tuning parameters come from `config/sherpa_onnx.config`.

---

### Step 2: Create the KeywordSpotter
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
This loads the Zipformer ONNX model into memory. The model is a neural network trained
to spot specific words in a continuous audio stream in real time.

**What is a Zipformer?** A type of Transformer-based acoustic model optimised for
streaming (chunk-by-chunk) speech recognition. The "3.3M" refers to 3.3 million parameters
— small enough to run fast on CPU.

**What is GigaSpeech?** The training dataset — 10,000 hours of English audio from
podcasts, YouTube, audiobooks. The model was trained on this data.

---

### Step 3: Create a KWS Stream
```python
kws_stream = keyword_spotter.create_stream()
```
A "stream" in sherpa-onnx is a stateful object that holds the model's running memory
(context) for one ongoing listening session. Each time a keyword is detected, the stream
is discarded and a new one is created (to reset the model's context).

---

### Step 4: Start the Microphone
```python
device_stream = process_audio_stream()
```
This calls `listener.py`'s function to start the background mic thread. Audio chunks
will now begin filling `audio_queue`.

---

### Step 5: The Detection Loop
```python
while True:
    # 1. Get next audio chunk from the queue
    samples = audio_queue.get(timeout=0.1)  # waits up to 100ms for data

    # 2. Flatten 2D array (frames, channels) → 1D array (frames,)
    samples = samples.reshape(-1)

    # 3. Feed audio into the KWS stream
    kws_stream.accept_waveform(sample_rate, samples)

    # 4. Decode as long as the model has enough audio context
    while keyword_spotter.is_ready(kws_stream):
        keyword_spotter.decode_stream(kws_stream)

    # 5. Check if a keyword was found
    result = keyword_spotter.get_result(kws_stream)
    if result:
        print(f"🎯 KEYWORD DETECTED: {result}")
        kws_stream = keyword_spotter.create_stream()  # reset for next detection
```

#### Why `reshape(-1)`?
`sounddevice` gives audio as a 2D NumPy array: shape `(480, 1)` for mono audio.
`sherpa-onnx` expects a 1D array: shape `(480,)`.
`.reshape(-1)` flattens any shape into 1D.

#### Why `is_ready()` before `decode_stream()`?
The Zipformer model processes audio in **chunks** (it's a streaming model). `is_ready()`
checks whether the model has received enough audio to make a reliable decision for the
next chunk. You must keep calling `decode_stream()` until `is_ready()` returns False.

#### Why reset the stream after detection?
The KWS stream holds the model's internal state (its "memory" of recent audio). After
a keyword is found, that state is stale. Creating a fresh stream means the model starts
clean, ready to detect the next wake word without being confused by audio from the
previous trigger.

---

### Step 6: Graceful Shutdown
```python
except KeyboardInterrupt:
    print("🛑 Execution stopped safely by user.")
finally:
    device_stream.stop()
    device_stream.close()
```
When you press `Ctrl+C`:
1. The `KeyboardInterrupt` is caught — no crash
2. `finally` always runs, even after an exception
3. `.stop()` ends the background microphone thread
4. `.close()` releases the audio device so other programs can use it

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| `timeout=0.1` on `queue.get()` | Prevents the loop from blocking forever if no audio; allows the loop to stay responsive |
| `queue.Empty` caught with `continue` | If no audio chunk arrives in 100ms, just try again — not an error |
| Reset `kws_stream` after detection | Clears the model's internal state so the next detection starts fresh |
| `provider="cpu"` | Runs inference on CPU using ONNX Runtime — no GPU required |

---

## Configuration Reference (`config/sherpa_onnx.config`)

| Key | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `16000` | Audio must be 16kHz — this is what the model was trained on |
| `TOKEN` | path to `tokens.txt` | Maps model output integers back to characters |
| `ENCODER` | path to `.onnx` file | The encoder half of the Zipformer model |
| `DECODER` | path to `.onnx` file | The decoder half of the Zipformer model |
| `JOINER` | path to `.onnx` file | Combines encoder + decoder outputs to produce text |
| `KEYWORDS_FILE` | path to `keywords.txt` | The text file listing wake words to detect |
| `KEYWORD_SCORE` | `1.0` | Boost factor for keyword tokens (higher = easier to trigger) |
| `KEYWORD_THRESHOLD` | `0.25` | Minimum confidence score to count as a detection (lower = more sensitive) |
| `NUM_THREADS` | `1` | Number of CPU threads for inference |
| `MAX_ACTIVE_PATHS` | `4` | Beam width for beam search decoding (more paths = more accurate, slower) |
| `NUM_TRAILING_BLANKS` | `8` | How many blank/silence frames must follow a keyword before it is confirmed |
| `PROVIDER` | `cpu` | ONNX Runtime execution provider |
