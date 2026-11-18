#!/usr/bin/env bash
# GTA 6 Clipper setup: checks what this Mac needs, installs what's missing, says when it's ready.
# Safe to re-run any time.
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$SKILL_DIR/.venv"
MODELS="$SKILL_DIR/models"
mkdir -p "$MODELS"
ok()   { printf "  [ok]      %s\n" "$1"; }
inst() { printf "  [install] %s\n" "$1"; }
fail() { printf "  [MISSING] %s\n" "$1"; FAILED=1; }
FAILED=0

echo "GTA 6 Clipper setup"
if [[ "$(uname)" != "Darwin" ]]; then echo "Mac only for now."; exit 1; fi

# 1. Homebrew
if command -v brew >/dev/null 2>&1; then ok "Homebrew"; else
  fail "Homebrew (install from https://brew.sh then re-run setup)"; exit 1; fi

# 2. Command-line tools: ffmpeg (cutting/encoding), whisper-cpp (local transcript), deno (YouTube downloads)
for pair in "ffmpeg:ffmpeg" "whisper-cli:whisper-cpp" "deno:deno"; do
  bin="${pair%%:*}"; formula="${pair##*:}"
  if command -v "$bin" >/dev/null 2>&1; then ok "$formula"; else
    inst "$formula"; brew install "$formula" >/dev/null 2>&1 && ok "$formula" || fail "$formula (brew install $formula)"; fi
done

# 3. uv (fast Python + venv manager)
if command -v uv >/dev/null 2>&1 || [[ -x "$HOME/.local/bin/uv" ]]; then ok "uv"; else
  inst "uv"; curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 && ok "uv" || fail "uv"; fi
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"

# 4. Python environment: yt-dlp (always latest, sites change weekly), OpenCV (facecam finder), Pillow (captions)
if [[ ! -x "$VENV/bin/python" ]]; then inst "Python 3.12 environment"; "$UV" venv --python 3.12 "$VENV" >/dev/null 2>&1; fi
"$UV" pip install --python "$VENV/bin/python" -q -U "yt-dlp[default]" opencv-python-headless pillow numpy >/dev/null 2>&1 \
  && ok "Python packages (yt-dlp, opencv, pillow, numpy)" || fail "Python packages"

# 5. Whisper model (speech -> text, runs on this Mac). Reuse an existing one if present.
WHISPER_MODEL=""
for m in "$MODELS/ggml-small.en.bin" "$MODELS/ggml-small.bin" "$HOME/.cache/whisper-cpp/ggml-small.en.bin" "$HOME/.cache/whisper-cpp/ggml-small.bin"; do
  [[ -f "$m" ]] && WHISPER_MODEL="$m" && break; done
if [[ -z "$WHISPER_MODEL" ]]; then
  inst "Whisper small.en model (~465 MB)"
  curl -L -s -o "$MODELS/ggml-small.en.bin" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin \
    && WHISPER_MODEL="$MODELS/ggml-small.en.bin" || fail "whisper model"
fi
[[ -n "$WHISPER_MODEL" ]] && ok "Whisper model: $WHISPER_MODEL"

# 6. Face detector model (YuNet, ~230 KB) used to find the facecam box
YUNET="$MODELS/face_detection_yunet_2023mar.onnx"
if [[ ! -f "$YUNET" ]]; then
  inst "YuNet face detector"
  curl -L -s -o "$YUNET" https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx || fail "YuNet model"
fi
[[ -s "$YUNET" ]] && ok "Face detector" || fail "Face detector"

# 7. Fonts (macOS ships these)
[[ -f "/System/Library/Fonts/Supplemental/Arial Black.ttf" ]] && ok "Caption font (Arial Black)" || fail "Arial Black font"

# 8. Free space check: audio-only download keeps this small, but warn early
FREE_GB=$(df -g "$SKILL_DIR" | awk 'NR==2{print $4}')
if (( FREE_GB < 3 )); then echo "  [warn]    Only ${FREE_GB} GB free. Each stream needs ~0.5-1 GB while it runs."; else ok "Disk space (${FREE_GB} GB free)"; fi

cat > "$SKILL_DIR/config.json" <<EOF
{"whisper_model": "$WHISPER_MODEL", "yunet_model": "$YUNET"}
EOF

if [[ $FAILED -eq 0 ]]; then
  date > "$SKILL_DIR/.ready"
  echo; echo "READY. Say: clip this stream <link>   or   find me today's biggest GTA 6 streams and clip them"
else
  rm -f "$SKILL_DIR/.ready"; echo; echo "NOT READY: fix the [MISSING] items above and re-run setup."; exit 1
fi
