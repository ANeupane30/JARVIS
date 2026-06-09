# 04 — Speech to Text

**File:** `modules/voice/speech_to_text.py`
**Status:** ✅ Written — not yet wired into the main flow
**Library:** `faster-whisper`

---

## What This File Does

This file provides a **single function** that takes raw audio bytes and returns a
transcribed text string. It is the module that will convert what the user says (after
the wake word) into text that the LLM brain can understand.

It is currently **standalone** — the function exists and works, but `wakeup.py` does
not call it yet. That wiring will happen in the orchestrator (`core/orchestrator.py`).

---

## How It Works — Step by Step

### The Full Function
```python
def speech_to_text(audio_data):
    model_size = "base"
    model = WhisperModel(model_size, device="cpu", compute_type="default")

    segments, info = model.transcribe(io.BytesIO(audio_data), beam_size=5)

    try:
        for segment in segments:
            text = segment.text
        return text

    except Exception as e:
        return {"status": "error", "message": f"Error during transcription: {str(e)}"}
```

---

### Step 1: Load the Whisper Model
```python
model = WhisperModel("base", device="cpu", compute_type="default")
```

**What is Whisper?** An open-source speech recognition model by OpenAI, trained on
680,000 hours of multilingual audio. It converts speech to text with very high accuracy.

**What is faster-whisper?** A reimplementation of Whisper using CTranslate2, which is
a faster inference engine. It runs the same model but faster and with less memory.

**Model sizes available:**
| Size | Parameters | Relative Speed | Accuracy |
|---|---|---|---|
| `tiny` | 39M | Fastest | Lowest |
| `base` | 74M | Fast | Good ← currently used |
| `small` | 244M | Moderate | Better |
| `medium` | 769M | Slow | High |
| `large` | 1550M | Slowest | Highest |

`"base"` is a good starting point — accurate enough for commands, fast enough for
real-time use on CPU.

**`device="cpu"`** — runs on CPU, no GPU needed.
**`compute_type="default"`** — uses the default precision for the device (float32 on CPU).

---

### Step 2: Wrap Audio Bytes in a BytesIO Buffer
```python
segments, info = model.transcribe(io.BytesIO(audio_data), beam_size=5)
```

`faster-whisper`'s `transcribe()` method accepts either:
- A file path (string), or
- A file-like object (something with `.read()`)

Since we have raw audio bytes in memory (not saved to disk), we wrap them in
`io.BytesIO()` — this creates an in-memory "file" that `faster-whisper` can read
without touching the disk.

**`beam_size=5`** — controls the beam search during transcription. A beam size of 5
means the model tracks 5 candidate transcriptions at once and picks the best one.
Higher = more accurate but slower.

---

### Step 3: Extract Text from Segments
```python
for segment in segments:
    text = segment.text
return text
```

`transcribe()` returns a **lazy generator** of `Segment` objects. Each segment is a
chunk of the transcription (e.g., one sentence or phrase) with:
- `segment.text` — the transcribed text
- `segment.start` — start timestamp in seconds
- `segment.end` — end timestamp in seconds

The loop iterates through all segments and overwrites `text` each time, so only the
**last segment's text** is returned. This works fine for short commands but would need
to be changed (e.g., `" ".join(...)`) if transcribing longer audio with multiple segments.

---

### Step 4: Error Handling
```python
except Exception as e:
    return {"status": "error", "message": f"Error during transcription: {str(e)}"}
```

If something goes wrong (e.g., corrupt audio data), a dict with the error message is
returned instead of a string. Note: the caller will need to check the return type to
handle this correctly.

---

## Input / Output

| | Type | Description |
|---|---|---|
| **Input** | `bytes` | Raw audio data (e.g., from a recorded `.wav` file in memory) |
| **Output (success)** | `str` | The transcribed text string |
| **Output (error)** | `dict` | `{"status": "error", "message": "..."}` |

---

## Known Limitations / Things to Improve Later

| Issue | Detail |
|---|---|
| Model loaded on every call | `WhisperModel(...)` is inside the function, so the model is reloaded from disk each time `speech_to_text()` is called. This is slow. The model should be loaded once at startup and reused. |
| Only last segment returned | If audio has multiple sentences, only the last one is returned. Fix: join all segments. |
| No VAD (Voice Activity Detection) | The function transcribes whatever audio bytes it receives — it does not know if the audio contains speech or silence. |
| Return type inconsistency | Returns a `str` on success but a `dict` on error. Should return consistent types. |

---

## How It Will Be Used (Future)

Once the orchestrator is built, the flow will be:
```
Wake word detected (wakeup.py)
        │
        ▼
Capture user's command (new module — not yet built)
        │
        ▼
speech_to_text(audio_bytes)  ← this function
        │
        ▼
text string → sent to LLM brain (llm.py — not yet built)
```
