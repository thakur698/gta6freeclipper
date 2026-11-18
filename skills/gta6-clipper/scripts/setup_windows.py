"""Windows setup. Downloads Python 3.12, dependencies and a local speech model.

Run with any installed Python: python scripts/setup_windows.py
Use --check to verify an existing installation without changing it.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

SKILL = Path(__file__).resolve().parent.parent
PYTHON = SKILL / '.venv' / 'Scripts' / 'python.exe'


def call(cmd):
    subprocess.run([str(x) for x in cmd], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Use setup.sh on macOS.')
    if args.check:
        if not PYTHON.exists():
            sys.exit('NOT READY: missing Windows virtual environment')
        call([PYTHON, SKILL / 'scripts' / 'doctor.py'])
        return
    (SKILL / '.ready').unlink(missing_ok=True)
    if shutil.disk_usage(SKILL).free < 3 * 1024**3:
        sys.exit('NOT READY: setup needs at least 3 GB free')
    if not importlib.util.find_spec('uv'):
        call([sys.executable, '-m', 'pip', 'install', '--user', 'uv'])
    if not PYTHON.exists():
        call([sys.executable, '-m', 'uv', 'venv', '--python', '3.12', SKILL / '.venv'])
    call([sys.executable, '-m', 'uv', 'pip', 'install', '--python', PYTHON,
          '--upgrade', 'yt-dlp[default]', 'opencv-python-headless<5', 'pillow', 'numpy',
          'faster-whisper', 'av>=11,<17', 'psutil'])
    if not all(shutil.which(x) for x in ('ffmpeg', 'ffprobe')):
        if not shutil.which('winget'):
            sys.exit('NOT READY: install FFmpeg and FFprobe and add them to PATH, then rerun setup')
        call(['winget', 'install', '--exact', '--id', 'Gyan.FFmpeg', '--silent',
              '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'])
        links = Path(os.environ['LOCALAPPDATA']) / 'Microsoft' / 'WinGet' / 'Links'
        os.environ['PATH'] = str(links) + os.pathsep + os.environ.get('PATH', '')
        if not all(shutil.which(x) for x in ('ffmpeg', 'ffprobe')):
            sys.exit('NOT READY: reopen PowerShell after the FFmpeg installation and rerun setup')
    tools = SKILL / 'tools'
    tools.mkdir(exist_ok=True)
    # yt-dlp needs a JavaScript runtime for current YouTube extraction.
    if not shutil.which('deno') and not (tools / 'deno.exe').exists():
        if os.environ.get('PROCESSOR_ARCHITECTURE', '').upper() not in ('AMD64', 'ARM64'):
            sys.exit('NOT READY: Windows x64 or ARM64 required')
        archive = tools / 'deno.zip'
        urllib.request.urlretrieve(
            'https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip', archive)
        with zipfile.ZipFile(archive) as z:
            with z.open('deno.exe') as src, (tools / 'deno.exe').open('wb') as dst:
                shutil.copyfileobj(src, dst)
        archive.unlink()
    model = SKILL / 'models' / 'faster-whisper-small.en'
    call([PYTHON, '-c',
          'from faster_whisper import download_model; import sys; '
          'download_model("small.en", output_dir=sys.argv[1])', model])
    config = json.loads((SKILL / 'config.json').read_text(encoding='utf-8')) if (SKILL / 'config.json').exists() else {}
    config.update(transcription_backend='faster-whisper', faster_whisper_model=str(model),
                  whisper_device='cpu', whisper_compute_type='int8')
    (SKILL / 'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    call([PYTHON, SKILL / 'scripts' / 'doctor.py'])
    (SKILL / '.ready').write_text('Windows setup verified\n', encoding='utf-8')
    print('READY: Windows finished-stream and live clippers. No API keys needed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        sys.exit(f'NOT READY: {exc}')
