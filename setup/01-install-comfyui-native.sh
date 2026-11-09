#!/bin/bash
# Native ComfyUI-Installation für AMD (ROCm) mit uv
# - Nutzt Python 3.12, da PyTorch-ROCm keine Wheels für Python 3.14 (System-Python) anbietet
# - Installiert PyTorch ZUERST aus dem ROCm-Index, damit requirements.txt keine NVIDIA-Version zieht
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
ROCM_INDEX="https://download.pytorch.org/whl/rocm6.4"

echo "🐍 Erstelle Python 3.12 Umgebung (uv lädt Python bei Bedarf selbst herunter)..."
uv venv comfy_env --python 3.12 --clear
source comfy_env/bin/activate

[ -d ComfyUI ] || git clone https://github.com/comfyanonymous/ComfyUI.git

echo "🔥 Installiere PyTorch für AMD ROCm..."
uv pip install torch torchvision torchaudio --index-url "$ROCM_INDEX"

echo "📦 Installiere ComfyUI-Abhängigkeiten..."
uv pip install -r ComfyUI/requirements.txt

cd ComfyUI/custom_nodes
[ -d ComfyUI-Manager ] || git clone https://github.com/ltdrdata/ComfyUI-Manager.git
[ -d ComfyUI-VideoHelperSuite ] || git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
for n in ComfyUI-Manager ComfyUI-VideoHelperSuite; do
  [ -f "$n/requirements.txt" ] && uv pip install -r "$n/requirements.txt"
done
cd ../..

echo "🔎 GPU-Check:"
python -c "import torch; print('torch', torch.__version__, '| HIP:', torch.version.hip, '| GPU:', torch.cuda.is_available() and torch.cuda.get_device_name(0))"
echo "✅ Fertig. Start mit: ./start_comfyui.sh"
