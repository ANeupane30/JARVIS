import sounddevice as sd
import configparser
import queue
import numpy as np


# initializing the parser and Queue
config = configparser.ConfigParser()
audio_queue = queue.Queue()

# load the file
config.read("/config/sounddevice.config")
#loading values
sample_rate = config.SAMPLE_RATE
block_duration = config.BLOCK_DURATION
channels = config.CHANNELS



def audio_callback(indata, frames, time_info, status):
    "This function is called for each audio block by sounddevice"
    if status:
        print(status)
    # putting a copy of the audio data into the queue
    
def process_audio_stream():
    #start the stream
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        callback=audio_callback,
        blocksize=int(sample_rate * block_duration)
    )
    
    print("Listening for keywords...")
    with stream: 
        while True:
            # Get the raw 30ms block of audio
            audio_block = audio_queue.get()
            
            # TO-DO: Convert the audio block to features
            # add pass to your keyword spotting model
            
            
            pass