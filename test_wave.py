import wave
import numpy as np

if __name__ == "__main__":
    wr = wave.open("./sherpa-onnx-paraformer-zh-2023-03-28/test_wavs/0.wav")

    print(wr.getframerate())
    num_frame = wr.getnframes()
    all_frames = wr.readframes(num_frame)
    array = np.frombuffer(all_frames, dtype=np.float32)
    a = 1
    # print()