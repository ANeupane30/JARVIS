import speech_recognition as sr
from modules.voice.listener import speech_to_text

r = sr.Recognizer()
with sr.Microphone() as source:
    print("say something")
    audio = r.listen(source)
    
wav_data = audio.get_wav_data()

test = speech_to_text(wav_data)
print(test)