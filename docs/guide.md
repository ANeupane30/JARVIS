### Tools and Purpose
1. [pyttsx3](https://pypi.org/project/pyttsx3/): We are using this to convert text to speech offline.
2. [SpeechRecognition](https://pypi.org/project/SpeechRecognition/): We are using this to access microphone, and recode user speech.
3. [vosk](https://pypi.org/project/vosk/): we are using this to convert speech to text.
4. [python-decouple](https://pypi.org/project/python-decouple/): we are using this library to enforce strict separation between source code and application setting. 
5. [request](https://pypi.org/project/requests/): we are using request for ...


### More About tools in Detail
1. [pyttsx3](https://pypi.org/project/pyttsx3/): A cross-platform text to speech library with fully offline conversion support. This allows control over speed/rate of speech and tweak volume. For more information check [official document](https://pyttsx3.readthedocs.io/en/latest/index.html) 
   
2. [SpeechRecognition](https://pypi.org/project/SpeechRecognition/): A speech recognition library that supports multiple engines and APIs, including Google Web Speech (online) and CMU Sphinx (offline). It provides a straightforward interface to capture audio from a microphone or audio file and convert it to text. For more information check [official document](https://github.com/Uberi/speech_recognition#readme)

3. [requests](https://pypi.org/project/requests/): A simple and elegant HTTP library for making web requests. Used by JARVIS skills to call external APIs such as weather, news, and search services. Supports all major HTTP methods with built-in JSON response handling. For more information check [official document](https://requests.readthedocs.io/en/latest/)

4. [python-decouple](https://pypi.org/project/python-decouple/): A configuration management library that cleanly separates settings from source code. Reads API keys and sensitive credentials from a `.env` or `settings.ini` file at runtime, keeping secrets out of the repository. For more information check [official document](https://github.com/HBNetwork/python-decouple)

5. [vosk](https://pypi.org/project/vosk/): A fully offline speech recognition toolkit that supports over 20 languages and runs entirely on-device without sending audio to any external server. It is lightweight enough to run on low-powered hardware such as a Raspberry Pi and supports real-time streaming recognition, making it a privacy-friendly STT alternative for JARVIS. For more information check [official document](https://alphacephei.com/vosk/)