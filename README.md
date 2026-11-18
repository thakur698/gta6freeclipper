# GTA 6 Free Clipper

Windows and macOS skills for turning finished or live streams into vertical clips with captions.

Adapted from [vossashtonai/gta6-clipper](https://github.com/vossashtonai/gta6-clipper), by Ashton Voss AI, under the MIT license. This fork adds Windows support. The original license is preserved in LICENSE.

## Install in Codex

Copy both folders from `skills/` into your Codex skills directory (normally `%USERPROFILE%/.codex/skills` on Windows or `~/.codex/skills` on macOS), keeping them side by side.

On Windows, from the installed `gta6-clipper` folder:

```powershell
python scripts/setup_windows.py
```

Setup creates a Python 3.12 environment, installs dependencies, downloads the small.en speech model and Deno, and verifies readiness. FFmpeg and FFprobe are reused if installed; otherwise setup installs Gyan.FFmpeg through winget. Allow at least 3 GB free space. No additional API key is required.

Check an existing installation:

```powershell
.venv/Scripts/python.exe scripts/setup_windows.py --check
```

On macOS run `bash scripts/setup.sh` instead (requires Homebrew).

## Use

On your next Codex turn, ask `clip this stream` with a YouTube, Twitch or Kick URL, or `live clip` with a live stream URL. The agent selects highlights; transcription and rendering run locally. Output defaults to `~/GTA6-Clips/`.

Windows uses Faster Whisper with CPU int8, Windows caption fonts, UTF-8 files, and a detached live recorder with cooperative shutdown. See each skill's SKILL.md for commands and workflow.

## Validation

Windows setup, local speech and word timestamps, a 1080x1920 render with audio and captions, and detached recorder status/stop were tested locally. External stream downloads and macOS were not retested for this fork.

`validation/check_windows.py` runs the offline integration check using installed skills. First create `validation/speech.wav` containing spoken English (for example using Windows speech synthesis), then run the check through the installed skill's `.venv/Scripts/python.exe`. Generated media, models, environments and private configuration are excluded from Git.
