# JARVIS — Technical Guide Index

This folder contains technical documentation written for the developer (you) to understand
exactly what each part of the project does, how it works, and how the pieces connect.

## Who is this for?
You — the developer. These guides explain the internal logic of the code in plain language
so you can come back after a break and immediately understand what's happening.

---

## Guide Files

| File | What it covers |
|---|---|
| [01_project_structure.md](01_project_structure.md) | Folder layout and what each directory is for |
| [02_audio_listener.md](02_audio_listener.md) | How the microphone is captured (`listener.py`) |
| [03_wake_word_detection.md](03_wake_word_detection.md) | How the wake word is detected (`wakeup.py`) |
| [04_speech_to_text.md](04_speech_to_text.md) | How speech is converted to text (`transcriber.py`) |
| [05_configuration.md](05_configuration.md) | How config files work and what each setting does |
| [06_speaker.md](06_speaker.md) | Multiprocess TTS design (`speaker.py`) |
| [07_audio_orchestrator.md](07_audio_orchestrator.md) | Main event loop + diagnostic orchestrator |
| [08_brain.md](08_brain.md) | LLM integration, MCP client, and response formatting |

---

## Current Data Flow (What Works Today)

```
App startup
    │
    ├── DLL preload (Windows: onnxruntime before sherpa_onnx)
    ├── start_audio_stream()   ← mic stream starts once, runs forever
    └── prewarm()              ← TTS subprocess starts while KWS model loads

Microphone
    │
    ▼
listener.py ──► audio_queue (thread-safe Queue)
                      │
                      ▼
                 wakeup.py
           sherpa-onnx KWS model
              reads audio_queue
                      │
              wake word detected?
                      │
                     YES
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
    flush audio_queue     speak("How can I help you")
    (discard wake-word     (non-blocking → TTS subprocess)
      audio chunks)
             │
             ▼
       transcriber.py
   listen_and_transcribe()
   reads audio_queue until
   silence (RMS threshold)
             │
             ▼
      faster-whisper STT
             │
             ▼
       transcript string
             │
             ▼
       jarvis/brain/llm.py
       llm_response(transcript)
       OpenRouter API → openai/o4-mini
             │
             ▼
   response_formatter.py
   complete_json_response(data)
   extracts text from JSON
             │
             ▼
       speak(llm_result)
       (non-blocking → TTS subprocess)
             │
             ▼
     [returns to KWS loop]
```

> **MCP Note:** `jarvis/brain/mcp_client.py` and `mcp_server/server.py` are implemented
> but not yet wired into the main loop. The MCP tool-use loop (LLM calls a tool → gets
> result → responds) is the next integration milestone.

---

## Package Structure

The project uses the `jarvis` Python package (importable via `import jarvis`):

```
jarvis/
├── __init__.py
├── component/              ← Low-level hardware/IO modules
│   ├── listener.py         ✅ Working — mic capture
│   ├── wakeup.py           ✅ Working — wake word detection
│   ├── transcriber.py      ✅ Working — silence-aware STT
│   ├── speaker.py          ✅ Working — multiprocess TTS (pyttsx3 + SAPI5)
│   └── response_formatter.py  ✅ Working — parses OpenRouter JSON responses
├── orchestrator/           ← Wires components into a loop
│   ├── audio_orchestrator.py  ✅ Working — production main loop (includes LLM call)
│   └── test_orchestrator.py   ✅ Working — diagnostic loop with timing logs
├── brain/                  ← LLM reasoning and memory
│   ├── llm.py              ✅ Working — OpenRouter API integration
│   ├── mcp_client.py       ✅ Implemented — MCP client (not yet wired into loop)
│   ├── memory.py           🔲 Empty — planned
│   └── response.py         🔲 Empty — planned
└── skills/                 ← Specific capabilities
    └── example1_skill1.py  🔲 Placeholder

mcp_server/
└── server.py               ✅ Implemented — MCP server with get_weather stub
```
