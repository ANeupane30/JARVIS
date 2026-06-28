from jarvis.component.listener import start_audio_stream, audio_queue
from jarvis.component.wakeup import kws
from jarvis.component.transcriber import listen_and_transcribe
from jarvis.component.speaker import speak, prewarm
from jarvis.component.response_formatter import complete_json_response
from jarvis.brain.llm import llm_response

import queue as q
import configparser



config = configparser.ConfigParser()
config.read("config/sounddevice.config")  # config for keyword spotter audio

# loading value for Keyword Spotter Audio
sample_rate = int(config['kws_audio']['SAMPLE_RATE'])
block_duration = float(config['kws_audio']['BLOCK_DURATION'])
channels = int(config['kws_audio']['CHANNELS'])

llm_call = False

def run():
    # start once — never stopped between kws and sr
    device_stream = start_audio_stream(sample_rate, channels, block_duration)
    prewarm() # process warms up while KWS is loading
    print('Listening....')

    try:
        while True:
            # kws reads from audio_queue
            keyword = kws()
            print("KWS Detected")
            speak("How can I help you")
            llm_call = True
            
            # flush queue — discard the keyword audio itself so
            # whisper doesn't transcribe "hey jarvis" as the command
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except q.Empty:
                    break

            # sr reads from the same audio_queue
            while llm_call:
                transcript = listen_and_transcribe(block_duration)
                print(f"You said: {transcript}")
                data = llm_response(transcript)
                llm_result = complete_json_response(data)
                print(llm_result)
                speak(llm_result)
                llm_call = False
            # calling LLM

    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        device_stream.stop()
        device_stream.close()
