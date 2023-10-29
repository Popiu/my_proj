from pathlib import Path
import librosa
import utils.argument_par as argument_par
import utils.recognizer_utils as recognizer_utils
import utils.wave_utils as wave_utils

MODEL_PATH = "./sherpa-onnx-paraformer-zh-2023-03-28/"
use_int8 = False

if __name__ == "__main__":
    args = argument_par.get_args()
    args.tokens = MODEL_PATH + "tokens.txt"
    if use_int8:
        args.paraformer = MODEL_PATH + "model.int8.onnx"
    else:
        args.paraformer = MODEL_PATH + "model.onnx"
    recognizer = recognizer_utils.create_recognizer(args)

    result = recognizer_utils.get_result(
        recognizer,
        "./sherpa-onnx-paraformer-zh-2023-03-28/test_wavs/my_recording.wav"
    )





