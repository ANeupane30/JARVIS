"""
This function activate after KWS is detected. It takes audio stream stores them until silence is detected.
Before processing stored audio it concatinate them and process all at once.  
"""

import numpy as np
import queue
from listener import audio_queue
from faster_whisper import WhisperModel
import numpy as np

silence_timeout: float = 4.0
max_duration: float = 15.0
threshold: float = 0.01
model = WhisperModel('base', device="cpu", compute_type="default")

def speech_to_text(audio_data: np.ndarray):
    """
    Transcribe a float32 numpy audio array to text.
    Accepts audio sampled at 16kHz, values in range [-1.0, 1.0].
    Returns an empty string if transcription fails.
    """

    try:
        segments, info = model.transcribe(audio_data, beam_size=5)
        
        return " ".join(seg.text for seg in segments).strip()
    
    except Exception as e:
        return {"status": "error", "message": f"Error during transcription: {str(e)}"}


def detect_silence(chunk: np.ndarray, threshold: float):
    """
    Return True if the RMS energy of the audio chunk is below threshold.
    threshold of 0.01 works for most quiet environments.
    Calibrate by printing RMS values during silence on your microphone.
    """
    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
    return rms < threshold

def listen_and_transcribe(block_duration):
    """
    Read from audio_queue until silence is detected, then transcribe.
    Uses detect_silence() to decide when to stop.
    Uses speech_to_text() to transcribe the collected buffer.
    Returns transcribed string, or empty string if nothing captured.
    """
    frames = []
    silent_chunks = 0
    silent_needed = int(silence_timeout / block_duration)
    max_chunks    = int(max_duration    / block_duration)

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
            silent_chunks = 0       # user still speaking, reset counter

    if not frames:
        return ""

    audio = np.concatenate(frames).astype(np.float32)
    return speech_to_text(audio)    # hand off to speech_to_text