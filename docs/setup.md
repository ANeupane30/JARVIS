# Setup & Installation Guide

Follow these steps to get the development environment running on your local machine.

## 1. Prerequisites
Before installing the dependencies, ensure you have the following:
* **Python 3.8+**: This project requires a modern Python environment. Check your version with `python --version`.
* **pip**: The Python package installer (usually included with Python).
* **Virtual Environment (Recommended)**: To avoid conflicts with other projects.

## 2. Installation

### Clone the Repository
```bash
git clone <your-repo-url>
cd JARVIS
```

### Create a Virtual Environment
It is highly recommended to use a virtual environment to keep dependencies isolated.
```bash
# Create the environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Install Dependencies
Install the required libraries listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

> **Note:** On Windows, `pyttsx3` requires the `pywin32` and `pypiwin32` packages which are already listed in `requirements.txt`. If you encounter issues, try running `pip install pywin32` separately.

## 3. Configuration

### Environment Variables (`.env`)
The application uses environment variables to manage personal settings.

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
Once the setup is complete, run JARVIS from the project root:
```bash
python main.py
```

JARVIS will:
1. Start the microphone stream
2. Wait for the wake word (e.g., "Hey JARVIS")
3. Say "How can I help you"
4. Listen for your command and transcribe it
5. Print the transcription (LLM integration coming soon)

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
* **Missing Dependencies:** If a library fails to install, ensure your `pip` is up to date: `pip install --upgrade pip`.
* **Microphone not detected:** Make sure your system default microphone is set correctly. `sounddevice` uses the system default input device.
* **`sherpa_onnx` model error:** Verify that all model files exist in `model/kws-zipformer/` and that `config/sherpa_onnx.config` paths are correct.
* **`pyttsx3` issues on Windows:** Ensure `pywin32` is installed and try running the script with administrator privileges if needed.
* **Environment Errors:** Double-check that your `.env` file is in the root folder and the keys match the names used in the code.
