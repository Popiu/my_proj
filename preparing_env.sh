pip install sherpa-onnx
pip install librosa
sudo apt-get install git-lfs
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/csukuangfj/sherpa-onnx-paraformer-zh-2023-03-28
cd sherpa-onnx-paraformer-zh-2023-03-28
git lfs pull --include "*.onnx"