"""Offline Windows integration check: real speech, render, concat and recorder stop."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

VOD = Path.home() / '.codex/skills/gta6-clipper'
LIVE = VOD.parent / 'gta6-live-clipper'
sys.path[:0] = [str(VOD / 'scripts'), str(LIVE / 'scripts')]
import gta6clip as g
import live

ROOT = Path(__file__).resolve().parent


def checked(cmd):
    r = g.run(cmd)
    if r.returncode:
        raise RuntimeError(r.stderr[-2000:])
    return r


def daemon(rd):
    # Local data producer exercises the real yt-dlp -> FFmpeg pipe without a network stream.
    g.YTDLP = [sys.executable, str(ROOT / 'producer.py')]
    live.SEG = 1
    d = live.Daemon(rd)
    d.chat = lambda: None
    d.process_segment = lambda *args: None
    d.run()


def main():
    rd = ROOT / "Windows test's clips"
    rd.mkdir(exist_ok=True)
    words = g.transcribe(ROOT / 'speech.wav', rd / 'words', words=True)
    assert len(words) >= 5, words
    print('PASS: local speech transcription with word timestamps', flush=True)
    src = ROOT / 'source.ts'
    checked(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
             'testsrc2=size=640x360:rate=30', '-i', str(ROOT / 'speech.wav'),
             '-t', '6', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '30',
             '-c:a', 'aac', '-f', 'mpegts', str(src)])
    # Check FFmpeg concat with drive letters, spaces and apostrophes.
    lst = rd / 'concat.txt'
    lst.write_text(live.concat_entry(src), encoding='utf-8')
    concat = rd / 'joined.ts'
    checked(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
             '-i', str(lst), '-c', 'copy', str(concat)])
    c = {'_s': 0, '_e': 4, 'title': 'Windows clip test', 'hook': 'WINDOWS CLIP TEST',
         'caption': 'Unicode works: café 🎮', 'score': 8, 'category': 'test', 'layout': 'gameplay'}
    out, mode = g.render_one(rd, {'streamer': 'Local test', 'webpage_url': 'local test'}, c,
                              1, None, True, local_src=concat, src_start=0)
    meta = json.loads(checked(['ffprobe', '-v', 'error', '-show_entries',
                              'stream=width,height:format=duration', '-of', 'json', str(out)]).stdout)
    assert meta['streams'][0]['width'] == 1080 and meta['streams'][0]['height'] == 1920, meta
    assert 3.8 <= float(meta['format']['duration']) <= 4.3, meta
    assert '🎮' in out.with_suffix('.txt').read_text(encoding='utf-8')
    print(f'PASS: real 1080x1920 render, audio, captions and Unicode: {out}', flush=True)
    live_rd = ROOT / 'live test'
    live_rd.mkdir(exist_ok=True)
    live.jsave(live_rd / 'stream.json', {'url': 'local', 'streamer': 'test', 'window_min': 1})
    live.jsave(live_rd / 'state.json', {'windows': 0})
    (live_rd / 'stop.request').unlink(missing_ok=True)
    producer = '''import sys, time
from pathlib import Path
data = (Path(__file__).parent / 'source.ts').read_bytes()
for i in range(0, len(data), 8192):
    sys.stdout.buffer.write(data[i:i+8192]); sys.stdout.buffer.flush(); time.sleep(0.15)
time.sleep(120)
'''
    (ROOT / 'producer.py').write_text(producer, encoding='utf-8')
    with (live_rd / 'daemon.log').open('wb') as log:
        p = subprocess.Popen([sys.executable, __file__, '--daemon', str(live_rd)],
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                             creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    (live_rd / 'pid').write_text(str(p.pid), encoding='utf-8')
    try:
        time.sleep(7)
        assert live.process_alive(p.pid), 'Detached daemon died'
        live.cmd_status(argparse.Namespace(runs=[str(live_rd)]))
        assert p.poll() is None, 'Status terminated the recorder'
        live.cmd_stop(argparse.Namespace(runs=[str(live_rd)]))
        p.wait(timeout=35)
        st = live.jload(live_rd / 'state.json', {})
        assert st.get('ended'), (st, (live_rd / 'daemon.log').read_text())
        assert list((live_rd / 'buffer').glob('*.ts')), 'No finalized segments'
        print('PASS: detached live recorder, non-destructive status, cooperative stop and finalized segments')
    finally:
        if p.poll() is None:
            import psutil
            proc = psutil.Process(p.pid)
            for child in proc.children(recursive=True):
                child.kill()
            proc.kill()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        daemon(Path(sys.argv[2]))
    else:
        main()
