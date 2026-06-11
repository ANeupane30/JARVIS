from jarvis.component.listener import start_audio_stream, audio_queue
from jarvis.component.wakeup import kws
from jarvis.component.transcriber import listen_and_transcribe
import queue as q
import configparser

config = configparser.ConfigParser()
config.read("config/sounddevice.config")  # config for keyword spotter audio

# loading value for Keyword Spotter Audio
sample_rate = int(config['kws_audio']['SAMPLE_RATE'])
block_duration = float(config['kws_audio']['BLOCK_DURATION'])
channels = int(config['kws_audio']['CHANNELS'])



def run():
    # start once — never stopped between kws and sr
    device_stream = start_audio_stream(sample_rate, channels, block_duration)
    print('Listening....')

    try:
        while True:
            # kws reads from audio_queue
            keyword = kws()
            print(f"Detected: {keyword}")

            # flush queue — discard the keyword audio itself so
            # whisper doesn't transcribe "hey jarvis" as the command
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except q.Empty:
                    break

            # sr reads from the same audio_queue
            transcript = listen_and_transcribe(block_duration)
            print(f"You said: {transcript}")

    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        device_stream.stop()
        device_stream.close()
