# 02 — Audio Listener

**File:** `jarvis/component/listener.py`
**Status:** ✅ Working
**Library:** `sounddevice`

---

## What This File Does

This file is responsible for one thing: **capture raw audio from your microphone and make
it available to the rest of the program**.

It does NOT process or analyze the audio. It simply captures it and hands it off.

---

## How It Works — Step by Step

### Step 1: Create a Shared Queue
```python
audio_queue = queue.Queue()
```
A `Queue` is a thread-safe container — like a conveyor belt. One thread puts audio onto it,
another thread takes audio off. It handles synchronization automatically so there are no
race conditions.

This `audio_queue` is a **module-level global** exported from `listener.py`.
Other modules import it directly:
```python
from jarvis.component.listener import audio_queue
```

---

### Step 2: The Callback Function
```python
def audio_callback(indata, frames, time_info, status):
    "This function is called for each audio block by sounddevice"
    if status:
        print(status)
    audio_queue.put(indata.copy())
```
`sounddevice` calls this function **automatically** every 30ms with a fresh chunk of audio.
You never call this function yourself — the library does.

- `indata` — a NumPy array of shape `(frames, channels)` containing the raw audio samples
- `indata.copy()` — a copy is made because `indata` is a buffer that gets overwritten;
  without `.copy()` you'd be reading garbage data later
- The copy is placed into `audio_queue` for the main loop to pick up

---

### Step 3: Start the Stream
```python
def start_audio_stream(sample_rate, channels, block_duration):
    """Start background audio stream. Returns the stream object."""
    stream = sd.InputStream(
        samplerate=sample_rate,
        dtype='float32',
        channels=channels,
        callback=audio_callback,
        blocksize=int(sample_rate * block_duration)
    )
    stream.start()
    return stream
```
- `sd.InputStream` sets up the microphone tap but doesn't start it yet
- `.start()` launches a **background thread** managed by `sounddevice`/PortAudio
- The stream object is returned so the caller can `.stop()` and `.close()` it later
- Parameters (sample rate, channels, block duration) are passed in — the caller reads
  them from `config/sounddevice.config`. This keeps the listener free of config logic.

> **Note:** The function was renamed from `process_audio_stream()` (as it appeared in
> earlier documentation) to `start_audio_stream()` to better reflect its purpose.

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| `queue.Queue` for sharing audio | Thread-safe — no locks needed manually |
| `indata.copy()` | Prevents reading corrupted/overwritten buffer data |
| `dtype='float32'` | Sherpa-ONNX and faster-whisper both expect float32 samples in range [-1.0, 1.0] |
| 30ms block size (`0.03s`) | Small enough for real-time KWS; large enough to be efficient. At 16kHz: 16000 × 0.03 = 480 samples/chunk |
| Returns the stream object | Lets the caller clean up properly with `.stop()` + `.close()` |
| Config passed as arguments | Keeps `listener.py` decoupled from `configparser`; the orchestrator owns config reading |

---

## What It Does NOT Do
- It does not filter or process audio
- It does not detect silence or voice activity
- It does not save audio to disk
- It does not directly communicate with the KWS model

All of that is handled downstream by `wakeup.py` and `transcriber.py`.

---

## Exported Interface

Other files import from this module:
```python
from jarvis.component.listener import start_audio_stream, audio_queue
```

| Export | Type | Purpose |
|---|---|---|
| `start_audio_stream(sample_rate, channels, block_duration)` | function | Call once to start the mic stream; returns stream object |
| `audio_queue` | `queue.Queue` | Read from this to get audio chunks; shared by `wakeup.py` and `transcriber.py` |
