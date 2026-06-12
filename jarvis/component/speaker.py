"This file contains a function to make jarvis speak."
"""
For now runAndWait() blocking the audio stream when Jarvis is speaking
So the potential solution is to create a background thread for TTS. 
Create a queue for speak and use separate process to speak once queue is empty close the process
Make speak function to take a text and response that text, text can be from 
"""


import pyttsx3
from multiprocessing import Queue, Process, Event

speak_queue = Queue()
tts_process = None
event = Event()


def speak_worker(speak_queue, done_event):
    #initiating pyttsx3 engine and queue
    engine = pyttsx3.init()

    # setting speak speed
    engine.setProperty("rate", 200) 

    # setting female voice
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    
    while True:
        # getting the response to speak from queue
        text = speak_queue.get()
        # if nothing in queue end the function
        if text is None:
            break
        # speak once we get anything in queue
        done_event.clear()  # say speaking hasn't began yet
        engine.say(text)
        engine.runAndWait()
        done_event.set() # speaking is completed


def mp_running():
    "Start a new process if one is not already alive"
    
    global tts_process
    # init multiprocessing for speaker       
    if tts_process is None or not tts_process.is_alive():
        tts_process = Process(target = speak_worker, args=(speak_queue, event,), daemon=True)
        tts_process.start()
        
def speak(response):
    speak_queue.put(response) # adding response back to queue
    mp_running() # ensures multiprocessing running
    

def speak_and_wait(response, timeout: float= 5.0):
    "Blocking waits untill speech finishes before returning"
    event.clear()
    speak_queue.put(response)
    mp_running()
    event.wait(timeout)

# defining a function to stop speaking if user calls Jarvis while speaking or when detecting words like Jarvis Stop or Stop 
def terminate_speaking():
    """
    Instantly kill TTS and discard anything pending.
    Next speak() call will create a fresh process automatically.
    """
    global tts_process
    # discard pending items first
    while not speak_queue.empty(): # if queue list is not empty
        try:
            speak_queue.get_nowait()
        except Exception:
            break
    
    #Terminate process
    if tts_process is not None and tts_process.is_alive(): # checks if tts_process is exist before checking it is alive or not 
        tts_process.terminate() 
        tts_process.join(timeout=1.0)  # waits for 1 second before ignoring if not closed till then 
        
    tts_process = None
    event.set()
    mp_running()



 