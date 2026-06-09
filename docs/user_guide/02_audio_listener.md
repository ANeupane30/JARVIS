# 02 — Audio Listener

**File:** `modules/voice/listener.py`
**Status:** ✅ Working
**Library:** `sounddevice`

---

## What This File Does

This file is responsible for one thing: **capture raw audio from your microphone and make
it available to the rest of the program**.

It does NOT process or analyze the audio. It simply captures it and hands it off.

---

## How It Works — Step by Step

### Step 1: Load Config
```python
config = configparser.ConfigParser()
config.read("config/sounddevice.config")

sample_rate   = int(config['audio']['SAMPLE_RATE'])    # 16000 Hz
block_duration = float(config['audio']['BLOCK_DURATION']) # 0.03 seconds = 30ms
channels      = int(config['audio']['CHANNELS'])        # 1 (mono)
```
Settings are read from `config/sounddevice.config` instead of being hardcoded.
This means you can change them without touching this file.

---

### Step 2: Create a Shared Queue
```python
audio_queue = queue.Queue()
```
A `Queue` is a thread-safe container — like a conveyor belt. One thread puts audio onto it,
another thread takes audio off. It handles synchronization automatically so there are no
race conditions.

This `audio_queue` is exported (imported by `wakeup.py`) so other modules can consume
the audio data.

---

### Step 3: The Callback Function
```python
def audio_callback(indata, frames, time_info, status):
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

### Step 4: Start the Stream
```python
def process_audio_stream():
    stream = sd.InputStream(
        samplerate=sample_rate,      # 16000 samples per second
        dtype='float32',             # each sample is a 32-bit float between -1.0 and 1.0
        channels=channels,           # 1 channel (mono)
        callback=audio_callback,     # called automatically every blocksize samples
        blocksize=int(sample_rate * block_duration)  # 16000 * 0.03 = 480 samples per chunk
    )
    stream.start()
    return stream
```
- `sd.InputStream` sets up the microphone tap but doesn't start it yet
- `.start()` launches a **background thread** managed by `sounddevice`/PortAudio
- The stream object is returned so the caller can `.stop()` and `.close()` it later

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| `queue.Queue` for sharing audio | Thread-safe — no locks needed manually |
| `indata.copy()` | Prevents reading corrupted/overwritten buffer data |
| `dtype='float32'` | Sherpa-ONNX expects float32 samples in range [-1.0, 1.0] |
| 30ms block size (`0.03s`) | Small enough for real-time KWS; large enough to be efficient |
| Returns the stream object | Lets the caller clean up properly with `.stop()` + `.close()` |

---

## What It Does NOT Do
- It does not filter or process audio
- It does not detect silence or voice activity
- It does not save audio to disk
- It does not directly communicate with the KWS model

All of that is handled downstream by `wakeup.py`.

---

## Exported Interface

Other files import from this module:
```python
from listener import process_audio_stream, audio_queue
```

| Export | Type | Purpose |
|---|---|---|
| `process_audio_stream` | function | Call once to start the mic stream |
| `audio_queue` | `queue.Queue` | Read from this to get audio chunks |
