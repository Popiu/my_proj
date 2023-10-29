import wave
import numpy as np

def read_wave(wave_filename):
    # wr = wave.open(file_path)
    # num_frame = wr.getnframes()
    # all_frames = wr.readframes(num_frame)
    # array = np.frombuffer(all_frames, dtype=np.uint8)
    # # normalize this array to
    # sample_rate = wr.getframerate()
    # return sample_rate, array
    with wave.open(wave_filename) as f:
        assert f.getnchannels() == 1, f.getnchannels()
        assert f.getsampwidth() == 2, f.getsampwidth()
        num_samples = f.getnframes()
        samples = f.readframes(num_samples)
        samples_int16 = np.frombuffer(samples, dtype=np.int16)
        samples_float32 = samples_int16.astype(np.float32)
        samples_float32 = samples_float32 / 32768
        return samples_float32, f.getframerate()
