"This file contains a function to make jarvis speak"

import pyttsx3
from wakeup import kws

response = 'Hi, I am Alexa. How can I help you'
#initiating pyttsx3 engine
engine = pyttsx3.init()

rate = engine.getProperty("rate")  # getting details of current speaking rate
print(rate)  # printing current voice rate
engine.setProperty("rate", 125) 

voice = engine.getProperty('voice')
engine.setProperty('voice', voice[1].id)

kws_activate = kws()

while kws_activate:
    engine.say(response)
    engine.runAndWait()
    engine.stop()