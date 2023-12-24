from pathlib import Path
import librosa
import utils.argument_par as argument_par
import utils.recognizer_utils as recognizer_utils
import utils.wave_utils as wave_utils

MODEL_PATH = "./my_models/"
DATA_PATH = "./my_dataset/test_wavs/"
use_int8 = True

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
        DATA_PATH + "0.wav"
    )
    print(result.result.text)





