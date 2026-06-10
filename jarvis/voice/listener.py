import sounddevice as sd
import configparser
import queue

"""
For now this file contains two function audio_callback() and process_audio_stream(). audio_callback()
stores short audio clips in queue for processing. Where as process_audio_stream() starts the stream once
and sounddevice's background thread runs continuously in background and collect the audio clip. 
"""

# # initializing  Queue
audio_queue = queue.Queue()

# config for detecting silence
silence_timeout : float = 1.5   #stop after this many seconds of silence
max_duration: float = 15.0     # safety cap for long audio
threshold: float = 0.01



def audio_callback(indata, frames, time_info, status):
    "This function is called for each audio block by sounddevice"
    if status:
        print(status)
    # putting a copy of the audio data into the queue
    audio_queue.put(indata.copy())
    
def start_audio_stream(sample_rate, channels, block_duration):
    """Start background audio stream. Returns the stream object."""
    #start the stream
    stream = sd.InputStream(
        samplerate=sample_rate,
        dtype='float32',
        channels=channels,
        callback=audio_callback,
        blocksize=int(sample_rate * block_duration)
    )
    
    #starting background listening
    stream.start()  # this line starts the sound device background thread. 
    return stream
