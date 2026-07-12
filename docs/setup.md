# Setup & Installation Guide

Follow these steps to get the development environment running on your local machine.

## 1. Prerequisites
Before installing the dependencies, ensure you have the following:
* **Python 3.12+**: This project requires Python 3.12 or newer. Check your version with `python --version`.
* **uv**: The project uses `uv` for dependency management. Install from [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/).
* **OpenRouter API Key**: Required for LLM responses. Sign up at [https://openrouter.ai/](https://openrouter.ai/).

## 2. Installation

### Clone the Repository
```bash
git clone <your-repo-url>
cd JARVIS
```

### Install Dependencies with uv
```bash
uv sync
```
This reads `pyproject.toml` and `uv.lock` and installs all dependencies into `.venv` automatically.

> **Note:** On Windows, `pyttsx3` requires `pywin32`. It is already listed in `pyproject.toml`. If you encounter COM errors, try running `pip install pywin32` inside the venv and then `python -m pywin32_postinstall -install`.

## 3. Configuration

### Environment Variables (`.env`)
The application uses environment variables to manage personal settings and API keys.

1. Copy the example file:
   ```bash
   # On Windows PowerShell:
   copy .env.example .env
   # On macOS/Linux:
   cp .env.example .env
   ```
2. Open the `.env` file and fill in your values:
   ```
   BOT_NAME=JARVIS
   USER_NAME=YourName
   OPENROUTER_API_KEY=sk-or-your-key-here
   ```
> **Note:** Never commit your `.env` file to version control. It is already listed in `.gitignore`.

### Audio Configuration (`config/sounddevice.config`)
Controls microphone capture settings. Default values work for most setups:
```ini
[kws_audio]
SAMPLE_RATE = 16000
BLOCK_DURATION = 0.03
CHANNELS = 1
```

### Wake Word Configuration (`config/sherpa_onnx.config`)
Controls the keyword spotting model. Paths point to the downloaded model files under `model/kws-zipformer/`.
To tune sensitivity, see [`docs/user_guide/05_configuration.md`](user_guide/05_configuration.md).

### KWS Model Files (`model/kws-zipformer/`)
The Sherpa-ONNX wake word model files must be present in `model/kws-zipformer/`. These include:
- `encoder-epoch-12-avg-2-chunk-16-left-64.onnx`
- `decoder-epoch-12-avg-2-chunk-16-left-64.onnx`
- `joiner-epoch-12-avg-2-chunk-16-left-64.onnx`
- `tokens.txt`
- `keywords.txt`

These files are **not committed to git** (large binary files). Download them from the
[sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases) or use the provided setup scripts.

## 4. Running the Application
Once the setup is complete, activate the virtual environment and run JARVIS from the project root:
```bash
# Activate the virtual environment
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# Run JARVIS
python main.py
```

JARVIS will:
1. Preload DLLs and start the audio stream
2. Prewarm the TTS subprocess
3. Wait for the wake word (e.g., "Hey JARVIS")
4. Say "How can I help you"
5. Listen for your command and transcribe it
6. Send the transcript to the LLM (OpenRouter / `openai/o4-mini`)
7. Speak the LLM's response back to you
8. Return to listening for the next wake word

Press `Ctrl+C` to stop safely.

## 5. Using the Setup Scripts
Convenience scripts are available in `scripts/`:

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

**macOS/Linux:**
```bash
bash scripts/setup.sh
```

## Troubleshooting
* **`uv sync` fails:** Make sure `uv` is installed (`pip install uv`) and that you are running Python 3.12+.
* **Microphone not detected:** Make sure your system default microphone is set correctly. `sounddevice` uses the system default input device.
* **`sherpa_onnx` model error:** Verify that all model files exist in `model/kws-zipformer/` and that `config/sherpa_onnx.config` paths are correct.
* **`pyttsx3` no audio on Windows:** This is the known SAPI5 stale COM bug — it is fixed in `speaker.py` by re-initialising the engine per utterance. If silence persists, ensure `pywin32` is installed correctly.
* **`OPENROUTER_API_KEY` error:** Ensure your `.env` file is in the project root and contains the key `OPENROUTER_API_KEY=sk-or-...`.
* **Environment Errors:** Double-check that your `.env` file is in the root folder and the keys match the names used in the code.
* **Windows DLL conflict (`onnxruntime` vs `sherpa_onnx`):** This is handled automatically in `main.py` — the script registers the venv's `onnxruntime` DLL directory before importing `sherpa_onnx`. Do not move the preload block.
