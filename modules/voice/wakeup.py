import openwakeword
from openwakeword.model import Model
from pathlib import Path
import numpy as np

model_dir = Path("./resources").resolve()
model_tflite = Path("./resources")

# downloading Jarvis model from openwakeword and saving in resource folder. 
openwakeword.utils.download_models(
    model_names=[],
    target_directory=str(model_dir)
)

# writing a wakeup function that takes arg: wakeup and 
def wakeup(wav_data):
    try:
        model = Model(wakeword_models=['./resources/melspectrogram.onnx'])
        np_converstion = np.frombuffer(wav_data, dtype=np.int16)
        frame = np.expand_dims(np_converstion,axis=0)
        return model.predict(frame)
    except Exception as e:
        return {"status": "error", "message": f"Error during  {str(e)}"}
        
