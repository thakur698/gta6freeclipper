"""Verify executable dependencies, speech model, detector, fonts and encoding."""
from pathlib import Path
import sys
import tempfile

import gta6clip as g


def main():
    import cv2
    import numpy as np
    import psutil
    import yt_dlp
    for name in ('ffmpeg', 'ffprobe', 'deno'):
        result = g.run([name, '--version' if name == 'deno' else '-version'])
        if result.returncode:
            raise RuntimeError(f'{name} failed: {result.stderr[-300:]}')
        print(f'[ok] {name}')
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    assert not detector.empty(), 'Missing face detector'
    assert g.font(84).getbbox('Windows captions')[3] > 20, 'Missing scalable caption font'
    with tempfile.TemporaryDirectory(prefix='gta6 check ') as folder:
        wav = Path(folder) / 'silence.wav'
        result = g.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
                        'anullsrc=r=16000:cl=mono', '-t', '1', str(wav)])
        assert result.returncode == 0, result.stderr
        g.transcribe(wav, Path(folder) / 'transcript', words=True)
    print('[ok] Python packages, detector, font, local speech model and transcription')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        sys.exit(f'NOT READY: {exc}')
