# 04 — Speech to Text (Transcriber)

**File:** `jarvis/component/transcriber.py`
**Status:** ✅ Working — wired into the orchestrator
**Library:** `faster-whisper`
**Depends on:** `listener.py` (imports `audio_queue`)

---

## What This File Does

This file provides the **speech capture and transcription pipeline**. After the wake word is
detected, the orchestrator calls `listen_and_transcribe()`, which:
1. Reads audio from `audio_queue` until silence is detected
2. Concatenates all collected audio frames into one NumPy array
3. Passes it to `speech_to_text()` which uses `faster-whisper` to transcribe

The result is a plain text string of what the user said.

---

## Module-Level Constants & Model Loading

```python
silence_timeout: float = 1.5   # seconds of silence before stopping capture
max_duration:    float = 15.0  # maximum recording length in seconds
threshold:       float = 0.01  # RMS energy below this = silence

model = WhisperModel('base', device="cpu", compute_type="default")
```

**The `WhisperModel` is loaded once at module import time.** This is a critical
performance improvement — loading the model on every function call would take several
seconds each time. Loading it once means the first call is slow but all subsequent calls
are fast.

---

## Functions

### `speech_to_text(audio_data: np.ndarray) → str`

```python
def speech_to_text(audio_data: np.ndarray):
    try:
        segments, info = model.transcribe(audio_data, beam_size=5)
        return " ".join(seg.text for seg in segments).strip()
    except Exception as e:
        return {"status": "error", "message": f"Error during transcription: {str(e)}"}
```

**Input:** A `float32` NumPy array of audio samples at 16kHz, values in [-1.0, 1.0].

**Key improvements over the original design:**
- Accepts a NumPy array directly (no `io.BytesIO` wrapping needed — `faster-whisper` now supports this natively)
- Joins **all segments** with spaces: `" ".join(seg.text for seg in segments).strip()`
  (the original version only returned the **last** segment, losing earlier parts of longer speech)
- Model is loaded once at module level (not inside the function)

**Output:**
- `str` — the transcribed text on success
- `dict` — `{"status": "error", "message": "..."}` on failure

> **Known issue:** The return type is inconsistent (str vs dict on error). The caller
> should check the type before using the result.

---

### `detect_silence(chunk: np.ndarray, threshold: float) → bool`

```python
def detect_silence(chunk: np.ndarray, threshold: float):
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    return rms < threshold
```

Returns `True` if the chunk is silent (below the RMS energy threshold).

**RMS (Root Mean Square)** is a measure of the average power of an audio signal.
For silence in a quiet room, RMS is typically < 0.01. During speech, it's much higher.

`threshold = 0.01` is a good starting point. You can calibrate it by printing RMS values
during silence on your specific microphone.

---

### `listen_and_transcribe(block_duration: float) → str`

```python
def listen_and_transcribe(block_duration):
    frames = []
    silent_chunks = 0
    silent_needed = int(silence_timeout / block_duration)   # = 1.5 / 0.03 = 50 chunks
    max_chunks    = int(max_duration    / block_duration)   # = 15.0 / 0.03 = 500 chunks

    print("Listening...")

    for _ in range(max_chunks):
        try:
            chunk = audio_queue.get(timeout=2.0)
        except queue.Empty:
            break

        frames.append(chunk.reshape(-1))

        if detect_silence(chunk, threshold):
            silent_chunks += 1
            if silent_chunks >= silent_needed:
                print("End of speech detected.")
                break
        else:
            silent_chunks = 0  # user still speaking, reset counter

    if not frames:
        return ""

    audio = np.concatenate(frames).astype(np.float32)
    return speech_to_text(audio)
```

#### How silence detection works:
- Each chunk is checked with `detect_silence()`
- A counter tracks consecutive silent chunks
- Once `silent_needed` consecutive silent chunks are seen (default: 50 × 30ms = **1.5 seconds** of silence), recording stops
- If the user speaks again before the counter reaches `silent_needed`, the counter resets

#### Safety limits:
- `timeout=2.0` on `queue.get()` — if no audio arrives in 2 seconds, stop (prevents hanging)
- `max_chunks` — hard cap of 15 seconds of recording regardless of silence

---

## Whisper Model Details

**What is Whisper?** OpenAI's speech recognition model, trained on 680,000 hours of
multilingual audio. Converts speech to text with high accuracy.

**What is faster-whisper?** A CTranslate2 reimplementation — same model, faster CPU inference.

| Size | Parameters | Relative Speed | Accuracy |
|---|---|---|---|
| `tiny` | 39M | Fastest | Lowest |
| `base` | 74M | Fast | Good ← currently used |
| `small` | 244M | Moderate | Better |
| `medium` | 769M | Slow | High |
| `large` | 1550M | Slowest | Highest |

`beam_size=5` — tracks 5 candidate transcriptions at once and picks the best.
Higher = more accurate but slower.

---

## Input / Output Summary

| | Type | Description |
|---|---|---|
| `listen_and_transcribe()` input | `float` (block_duration) | Used to calculate silence/max chunk counts |
| `listen_and_transcribe()` output | `str` | Full transcribed text, or `""` if nothing captured |
| `speech_to_text()` input | `np.ndarray` | Raw float32 audio samples at 16kHz |
| `speech_to_text()` output (success) | `str` | Transcribed text |
| `speech_to_text()` output (error) | `dict` | `{"status": "error", "message": "..."}` |

---

## Known Limitations / Things to Improve Later

| Issue | Detail |
|---|---|
| Inconsistent return types | `speech_to_text()` returns `str` on success but `dict` on error. Should raise an exception instead. |
| No VAD (Voice Activity Detection) | Silence is detected by RMS energy only. In noisy environments, background noise may prevent silence detection, causing max-duration cutoff. |
| Fixed silence threshold | `threshold = 0.01` is hardcoded. Should be moved to config for easy tuning. |
| Queue not flushed before capture | The orchestrator flushes the queue after wake word detection, but any residual wake-word audio may still appear in the queue briefly. |

---

## How It Is Used (Current Flow)

```
audio_orchestrator.py:
    kws()  →  wake word detected
    flush audio_queue  (discard wake word audio)
    speak("How can I help you")
    transcript = listen_and_transcribe(block_duration)
    print(f"You said: {transcript}")
    [Future] → send transcript to llm.py
```
