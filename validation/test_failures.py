"""Regression checks for recorder startup failure and empty highlight selections."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'skills/gta6-clipper/scripts'), str(ROOT / 'skills/gta6-live-clipper/scripts')]
import gta6clip as g
import live


class Failures(unittest.TestCase):
    def test_missing_recorder_executable_finishes_with_error(self):
        with tempfile.TemporaryDirectory() as folder:
            rd = Path(folder)
            live.jsave(rd / 'stream.json', {'url': 'local-test'})
            daemon = live.Daemon(rd)
            with patch.object(live.subprocess, 'Popen', side_effect=FileNotFoundError('missing tool')):
                daemon.record()
            state = live.jload(rd / 'state.json', {})
            self.assertFalse(state['recording'])
            self.assertIn('missing tool', state['error'])
            self.assertIn('ended_wall', state)

    def test_no_highlights_writes_empty_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            rd = Path(folder)
            (rd / 'picks').mkdir()
            (rd / 'transcript.json').write_text('[]', encoding='utf-8')
            (rd / 'stream.json').write_text(json.dumps({'streamer': 'test', 'title': 'test'}), encoding='utf-8')
            g.cmd_render(argparse.Namespace(run=folder, top=1, min_score=7, cookies=None, keep=False))
            summary = json.loads((rd / 'clips/summary.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['clips'], [])


if __name__ == '__main__':
    unittest.main()
