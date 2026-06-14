"This file contains a function to make jarvis speak."
"""
For now runAndWait() blocking the audio stream when Jarvis is speaking
So the potential solution is to create a background thread for TTS. 
Create a queue for speak and use separate process to speak once queue is empty close the process
Make speak function to take a text and response that text, text can be from 
"""


import pyttsx3
import multiprocessing
import queue

# Communication channels
speak_queue = multiprocessing.Queue()
stop_event = multiprocessing.Event()
tts_process = None

def speak_worker(q, stop_sig):
    """
    Persistent TTS worker — lives in a warm subprocess for the full app lifetime
    so the caller never pays the 2-5s SAPI5 cold-start cost.
 
    ROOT CAUSE FIX:
    pyttsx3 on Windows wraps SAPI5 via COM (Component Object Model).
    After the first runAndWait() completes, the internal SpVoice event sink
    and audio-output handle enter a stale state.  Subsequent say() +
    runAndWait() calls appear to succeed (no exception) but produce no audio.
 
    FIX: re-initialise the pyttsx3 engine on every speak call.
    Creating the engine object inside an already-running Python process costs
    ~100-300 ms, which is far cheaper than the 2-5 s process cold-start.
    Each iteration gets a brand-new COM SpVoice object with clean audio state.
    """
    while True:
        try:
            # Wait for text (timeout allows checking for process shutdown)
            text = q.get(timeout=1) 
            if text is None: break
            
            # Init engine ONCE at start of process life
            engine = pyttsx3.init()
            engine.setProperty("rate", 200)
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)

            # Internal callback to stop speaking if event is set
            def on_word(name, location, length):
                if stop_sig.is_set():
                    engine.stop() # This kills the current audio buffer

            engine.connect('started-word', on_word)
            
            stop_sig.clear() # Reset for new sentence
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            
            del engine

        except queue.Empty:
            continue 
        except Exception as e:
            print(f"TTS Worker Error: {e}")

def speak(response):
    # global tts_process
    # # Ensure process is warm
    # if tts_process is None or not tts_process.is_alive():
    #     tts_process = multiprocessing.Process(target=speak_worker, args=(speak_queue, stop_event), daemon=True)
    #     tts_process.start()
    
    speak_queue.put(response)

def prewarm():
    """
    Start the TTS worker process immediately at app launch.
    Call this once before the main loop so cycle 1 has no cold-start delay.
    """
    global tts_process
    if tts_process is None or not tts_process.is_alive():
        tts_process = multiprocessing.Process(
            target=speak_worker,
            args=(speak_queue, stop_event),
            daemon=True,
        )
        tts_process.start()
        
        
def terminate_speaking():
    # 1. Tell the engine to stop immediately via the Event
    stop_event.set()
    
    # 2. Clear the queue so it doesn't start the next sentence
    while True:
        try:
            speak_queue.get_nowait()
        except:
            break
            
    # Note: We do NOT terminate the process anymore to avoid the 5s reload lag.

 