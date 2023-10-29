from pathlib import Path
import librosa
import utils.argument_par as argument_par
import utils.recognizer_utils as recognizer_utils
import utils.wave_utils as wave_utils

if __name__ == "__main__":
    args = argument_par.get_args()
    args.tokens="./sherpa-onnx-paraformer-zh-2023-03-28/tokens.txt"
    args.paraformer="./sherpa-onnx-paraformer-zh-2023-03-28/model.int8.onnx"
    print(args)
    recognizer = recognizer_utils.create_recognizer(args)
    input_stream = recognizer.create_stream()
    samples, sample_rate = librosa.load("./sherpa-onnx-paraformer-zh-2023-03-28/test_wavs/my_recording.wav", sr=None, mono=True)
    input_stream.accept_waveform(sample_rate, samples)
    res = recognizer.decode_stream(input_stream)

