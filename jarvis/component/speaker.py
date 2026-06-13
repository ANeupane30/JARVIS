"This file contains a function to make jarvis speak."
"""
For now runAndWait() blocking the audio stream when Jarvis is speaking
So the potential solution is to create a background thread for TTS. 
Create a queue for speak and use separate process to speak once queue is empty close the process
Make speak function to take a text and response that text, text can be from 
"""


import pyttsx3
# from multiprocessing import Queue, Process
import multiprocessing
import queue
import time
# **************************************Testing Block*************************************

# Communication channels
speak_queue = multiprocessing.Queue()
stop_event = multiprocessing.Event()
tts_process = None

def speak_worker(q, stop_sig):
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

    while True:
        try:
            # Wait for text (timeout allows checking for process shutdown)
            text = q.get(timeout=1) 
            if text is None: break
            
            stop_sig.clear() # Reset for new sentence
            engine.say(text)
            engine.runAndWait()
        except queue.Empty:
            continue 
        except Exception as e:
            print(f"TTS Worker Error: {e}")

def speak(response):
    global tts_process
    # Ensure process is warm
    if tts_process is None or not tts_process.is_alive():
        tts_process = multiprocessing.Process(target=speak_worker, args=(speak_queue, stop_event), daemon=True)
        tts_process.start()
    
    speak_queue.put(response)

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

# ***************************************************************************









# speak_queue = Queue()
# tts_process = None



# def speak_worker(speak_queue):
#     #initiating pyttsx3 engine and queue
#     engine = pyttsx3.init()
#     engine.setProperty("rate", 200) # setting speak speed
#     voices = engine.getProperty('voices') 
#     engine.setProperty('voice', voices[1].id) # setting female voice
    
#     while True:
#         # getting the response to speak from queue
#         text = speak_queue.get()
#         # if nothing in queue end the function
#         if text is None:
#             break
#         # speak once we get anything in queue
#         try:
#             engine.say(text)
#             engine.runAndWait()
           
#         except Exception as e:
#             print(f"[TTS] Speak error: {e}")
#             # Attempt engine recovery
#             try:
#                 engine = pyttsx3.init()
#                 engine.setProperty("rate", 200)
#                 voices = engine.getProperty('voices')
#                 engine.setProperty('voice', voices[1].id)
#             except Exception as reinit_err:
#                 print(f"[TTS] Re-init failed: {reinit_err}")
#                 break

# def mp_running():
#     "Start a new process if one is not already alive"
    
#     global tts_process
#     # init multiprocessing for speaker       
#     if tts_process is None or not tts_process.is_alive():
#         tts_process = Process(target = speak_worker, args=(speak_queue,), daemon=True)
#         tts_process.start()
        
# def speak(response):
#     mp_running() # ensures multiprocessing running
#     speak_queue.put(response) # adding response back to queue
    

# # defining a function to stop speaking if user calls Jarvis while speaking or when detecting words like Jarvis Stop or Stop 
# def terminate_speaking():
#     """
#     Instantly kill TTS and discard anything pending.
#     Next speak() call will create a fresh process automatically.
#     """
#     global tts_process
#     # discard pending items first
#     while True: # if queue list is not empty
#         try:
#             speak_queue.get_nowait()
#         except queue.Empty:
#             break
    
#     #Terminate process
#     if tts_process is not None and tts_process.is_alive(): # checks if tts_process is exist before checking it is alive or not 
#         tts_process.terminate() 
#         tts_process.join(timeout=2.0)  # waits for 1 second before ignoring if not closed till then 
        
#     tts_process = None



 