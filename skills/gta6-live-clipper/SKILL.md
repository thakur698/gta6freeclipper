---
name: gta6-live-clipper
description: Clip YouTube, Twitch or Kick streams while they are live on Windows or macOS. Use for live clipping or managing a rolling stream recorder. Shares the gta6-clipper environment, transcription and renderer; for finished streams use gta6-clipper.
---

# GTA 6 LIVE Clipper

Same engine and output as the `gta6-clipper` skill (needs that one set up first, it shares its venv,
models and render code). The difference: nothing gets downloaded twice. The live stream is recorded into
1-minute segments on this computer, only the last `--buffer-min` minutes are kept, and clips are cut from them.

`L` = this skill's folder, `V` = the gta6-clipper folder next to it. Run:
`"$V/.venv/bin/python" "$L/scripts/live.py" <command>` on macOS.
On Windows PowerShell: `& "$V/.venv/Scripts/python.exe" "$L/scripts/live.py" <command>`.
Set `$V` and `$L` to the absolute installed folders. Write picks JSON as UTF-8. Quote paths.

If it says "Set up the GTA 6 clipper first", run `python "$V/scripts/setup_windows.py"` on Windows or `bash "$V/scripts/setup.sh"` on macOS.

## 1. Start

`start <url> [<url> ...]`: Twitch channel (`https://www.twitch.tv/kaicenat`), YouTube live link, or Kick.
Options: `--quality 720` (default; 1080 doubles disk), `--buffer-min 15`, `--window-min 5`,
`--cookies chrome` (Kick, age-restricted YouTube). Each stream gets a background recorder and a run folder.
Max 2 streams on a computer with 16 GB RAM (each transcribes a minute of audio every minute). If it says NOT LIVE, the
stream is finished: use gta6-clipper.

## 2. The loop (you run this until the stream ends or the user says stop)

Read `$V/references/picking.md` once before the first window. Then repeat:

1. `next <run> [<run> ...]` blocks up to 9 minutes until a new 5-minute window is ready (from any run) and
   prints it with the path to write. Use `--wait 45` and repeat as needed so tool waits stay bounded.
2. Write `picks/window_NNN.json` in THAT run folder, same format and same harsh rules as picking.md.
   `[]` when nothing qualifies (most windows). Windows overlap by 45 s: don't pick the same moment twice.
3. If you wrote any pick with score >= 7.5, run `clip <run>` right away. It renders from the buffer,
   skips anything already clipped, and prints the new clip paths.
4. Tell the user in ONE short line per new clip (title + path) and go back to step 1. No line for empty windows.

`next` printing "NO NEW WINDOW YET" just means keep looping. "STREAM ENDED" means run `clip` once more,
then report. Live clip bar is 7.5 (not 7): posting fast only matters if the clip is good.

Clips are ready ~5-8 min after the moment: up to 5 min for the window to close + picking + ~1 min render.
For a faster cadence use `--window-min 3` (more reads, more tokens).

## 3. Stop / check

- `status <run>`: recorder alive, minutes recorded, windows waiting, clips made.
- `stop <run>`: stops the recorder (the last partial window still gets written: pick it and clip).
- Clips live in `<run>/clips/` (mp4 + txt with title, caption, hashtags). Open with `Invoke-Item "<run>/clips"` on Windows or `open "<run>/clips"` on macOS.
- The buffer deletes itself as it rolls; old runs in `~/GTA6-Clips/live/` only get deleted if the user says so.

## Notes

- Chat speed is tracked on Twitch (read-only anonymous chat). YouTube/Kick live use loudness only.
- A moment older than the buffer can't be clipped (prints "out of buffer"). Keep up with the windows.
- The Claude session must stay open while live clipping. On Ollama/local models: one stream at a time.
