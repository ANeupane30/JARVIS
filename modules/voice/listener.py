import io
from faster_whisper import WhisperModel

"""
This functio
"""

def speech_to_text(audio_data):
    model_size = "base"
    model = WhisperModel(model_size, device="cpu", compute_type="default")
    # Reading the audi bytes using io.BytesIO
    segments, info = model.transcribe(io.BytesIO(audio_data), beam_size=5)
    
    try:
        # extracting text from segment
        for segment in segments:
            text = segment.text
        
        return text
    
    except Exception as e:
        return {"status": "error", "message": f"Error during transcription: {str(e)}"}
        

    