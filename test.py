import pyttsx3
engine = pyttsx3.init()

def externalLoop(x):
    for i in range(x):
        print('Testing')

engine.say('The quick brown fox jumped over the lazy dog.', 'fox')
engine.startLoop(True)
# engine.iterate() must be called inside externalLoop()
externalLoop(5)
engine.endLoop()

