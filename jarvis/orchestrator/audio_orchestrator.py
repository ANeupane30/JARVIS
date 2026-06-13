from jarvis.component.listener import start_audio_stream, audio_queue
from jarvis.component.wakeup import kws
from jarvis.component.transcriber import listen_and_transcribe
from jarvis.component.speaker import speak, speak_queue
import queue as q
import configparser
import jarvis.component.speaker as speaker
import time



config = configparser.ConfigParser()
config.read("config/sounddevice.config")  # config for keyword spotter audio

# loading value for Keyword Spotter Audio
sample_rate = int(config['kws_audio']['SAMPLE_RATE'])
block_duration = float(config['kws_audio']['BLOCK_DURATION'])
channels = int(config['kws_audio']['CHANNELS'])


# *************************************************************************************
"testing block"

def flush_audio():
    """Discard all stale audio chunks from the queue."""
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except q.Empty:
            break


def flush_speak():
    """Discard pending speech without killing the process."""
    while not speak_queue.empty():
        try:
            speak_queue.get_nowait()
        except Exception:
            break
        
def log(cycle: int, step: str, detail: str = ""):
    ms = int(time.time() * 1000) % 1000
    ts = time.strftime('%H:%M:%S.') + f"{ms:03d}"
    print(f"[{ts}] C{cycle} | {step:<38} {detail}")

def tts_state() -> str:
    proc      = speaker.tts_process
    alive     = proc is not None and proc.is_alive()
    pid       = proc.pid if proc is not None else "none"     
    qsize     = speaker.speak_queue.qsize()
    return (
        f"process={'ALIVE' if alive else 'DEAD '} pid={str(pid):<6} | "
        f"speak_q={qsize}"
    )

def divider(cycle: int, label: str):
    print(f"\n{'─'*65}")
    print(f"  CYCLE {cycle} — {label}")
    print(f"{'─'*65}")

def run():
    # start once — never stopped between kws and sr
    device_stream = start_audio_stream(sample_rate, channels, block_duration)
    # pre_start_speak_process = mp_running()  # warm-up a single, persistent TTS worker process at application startup
    print('Listening....')
    cycle = 0

    try:
        while True:
            cycle += 1
            divider(cycle, "START")
            # kws reads from audio_queue
            keyword = kws()
            print("KWS Detected")
            speak("How can I help you")
            log(cycle, "terminate_speaking(): after",  tts_state())
            print('Alexa Speaked')

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
        # pre_start_speak_process.close()


# **************************************************************************************


# def run():
#     # start once — never stopped between kws and sr
#     device_stream = start_audio_stream(sample_rate, channels, block_duration)
#     pre_start_speak_process = mp_running()
#     print('Listening....')

#     try:
#         while True:
#             # kws reads from audio_queue
#             keyword = kws()
#             print("KWS Detected")
#             speak_and_wait("How can I help you", timeout = 10.0)
#             print('Alexa Speaked')

#             # flush queue — discard the keyword audio itself so
#             # whisper doesn't transcribe "hey jarvis" as the command
#             while not audio_queue.empty():
#                 try:
#                     audio_queue.get_nowait()
#                 except q.Empty:
#                     break

#             # sr reads from the same audio_queue
#             transcript = listen_and_transcribe(block_duration)
#             print(f"You said: {transcript}")

#     except KeyboardInterrupt:
#         print("Stopping.")
#     finally:
#         device_stream.stop()
#         device_stream.close()
