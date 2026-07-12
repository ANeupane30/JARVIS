import os, sys
from pathlib import Path

if sys.platform == "win32":
    import importlib.util
    for pkg in ("onnxruntime", "sherpa_onnx"):
        spec = importlib.util.find_spec(pkg)
        if spec and spec.origin:
            base = Path(spec.origin).parent
            for sub in ("", "capi", "lib"):
                d = base / sub
                if d.exists():
                    os.add_dll_directory(str(d))
                    os.environ["PATH"] = str(d) + os.pathsep + os.environ["PATH"]

import onnxruntime  # preload the venv's 1.27 DLL before sherpa can touch System32's

from jarvis.orchestrator.audio_orchestrator import run

if __name__ == '__main__':
    test = run()