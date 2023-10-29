from pathlib import Path
import utils.argument_par as argument_par
import utils.recognizer_utils as recognizer_utils
import utils.wave_utils as wave_utils
# Make sure that the wave file is a single channel 16-bit encoded.
if __name__ == "__main__":
    print("Hello")
    args = argument_par.get_args()
    args.tokens="./sherpa-onnx-paraformer-zh-2023-03-28/tokens.txt"
    args.paraformer="./sherpa-onnx-paraformer-zh-2023-03-28/model.onnx"
    print(args)
    recognizer = recognizer_utils.create_recognizer(args)
    input_stream = recognizer.create_stream()
    samples, sample_rate = wave_utils.read_wave("./sherpa-onnx-paraformer-zh-2023-03-28/test_wavs/0.wav")
    input_stream.accept_waveform(sample_rate, samples)
    res = recognizer.decode_stream(input_stream)

