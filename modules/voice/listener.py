import sounddevice as sd
import configparser
import queue

"""
For now this file contains two function audio_callback() and process_audio_stream(). audio_callback()
stores short audio clips in queue for processing. Where as process_audio_stream() starts the stream once
and sounddevice's background thread runs continuously in background and collect the audio clip. 
"""

# initializing the parser and Queue
config = configparser.ConfigParser()
audio_queue = queue.Queue()
config.read("config/sounddevice.config") # load the file

#loading values
sample_rate = int(config['SAMPLE_RATE'])
block_duration = float(config['BLOCK_DURATION'])
channels = int(config['CHANNELS'])


def audio_callback(indata, frames, time_info, status):
    "This function is called for each audio block by sounddevice"
    if status:
        print(status)
    # putting a copy of the audio data into the queue
    audio_queue.put(indata.copy())
    
def process_audio_stream():
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
    