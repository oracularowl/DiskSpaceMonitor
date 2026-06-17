#!/usr/bin/env python3
"""
build_voiceover_natural.py

Rebuilds the Disk Space Monitor walkthrough video with a natural, human-sounding
neural voice using Microsoft Edge's free online neural voices (via the `edge-tts`
package). This is the human-like replacement for the old SAPI / "Microsoft Zira"
voice produced by create_voiceover_video.ps1.

It REUSES the existing slide PNGs in media/slides/ and only regenerates the
narration audio + the video. Nothing about your slides changes.

------------------------------------------------------------------------------
REQUIREMENTS (run once)
------------------------------------------------------------------------------
  1. Python 3.8+         https://www.python.org/downloads/  (tick "Add to PATH")
  2. ffmpeg on PATH      https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials)
  3. The edge-tts package:
         python -m pip install edge-tts
     (the script will offer to install it for you if it's missing)

  Internet is required while it runs: the neural voices are synthesized by
  Microsoft's online service. No API key, no account, free.

------------------------------------------------------------------------------
RUN
------------------------------------------------------------------------------
  python build_voiceover_natural.py

  Pick a different voice:
  python build_voiceover_natural.py --voice en-US-GuyNeural
  python build_voiceover_natural.py --voice en-US-JennyNeural
  python build_voiceover_natural.py --voice en-GB-RyanNeural

  List every available voice:
  python build_voiceover_natural.py --list-voices

  Slightly slower / faster delivery (default is -4%):
  python build_voiceover_natural.py --rate -8%

Output:
  media/DiskSpaceMonitor_v1_3_feature_walkthrough_natural.mp4
"""

import argparse
import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Narration, rewritten to sound like a person talking, not a manual being read.
# Contractions, shorter clauses, and natural punctuation give the neural voice
# room to breathe. The slide titles match the existing slide_XX.png images.
# ---------------------------------------------------------------------------
SLIDES = [
    {
        "title": "Disk Space Monitor v1.3",
        "voice": (
            "Hi, and welcome. This is Disk Space Monitor, version 1.3 — a small "
            "Windows app that keeps an eye on your free disk space for you. It's built "
            "with Python and Tkinter, and in this version it can even pause and resume "
            "a running 7-Zip extraction. Let's walk through how it works: picking a "
            "drive, setting a threshold, getting alerts, and a few real-world examples."
        ),
    },
    {
        "title": "Choose the Disk to Monitor",
        "voice": (
            "First, choose the drive you want to watch. The drop-down lists your "
            "Windows drives — your C drive, a D drive, a USB stick, whatever's "
            "connected. Plugged something in after opening the app? Just click Refresh "
            "Disks. Once a drive is selected, you'll see its total space, how much is "
            "used, how much is free, and the free-space percentage."
        ),
    },
    {
        "title": "Set a Free-Space Threshold",
        "voice": (
            "Next, decide what counts as low. In percent mode, you might say: warn me "
            "when the drive drops to ten percent free or less. That's great for general "
            "monitoring. In size mode, you set an actual amount — say, alert me when "
            "there's a hundred gigabytes left — which is handy when you need a "
            "specific amount of working room."
        ),
    },
    {
        "title": "Read the Live Status",
        "voice": (
            "The status panel updates on its own, every five seconds. The line to watch "
            "is Threshold reached. If it says Yes, your drive is already at or below the "
            "limit you set. Just below that, Popup monitoring tells you whether alerts "
            "are switched on. So you can keep an eye on things without turning on the "
            "pop-ups at all."
        ),
    },
    {
        "title": "Start Popup Monitoring",
        "voice": (
            "Ready for alerts? Click Start Monitoring. The app then checks your drive on "
            "a schedule — every thirty seconds, for example — and the moment the "
            "threshold is hit, a pop-up jumps to the front. Want to test it right now? "
            "Set percent free to one hundred and click Check Now. Every drive has a "
            "hundred percent or less free, so the alert fires straight away."
        ),
    },
    {
        "title": "Pause a Running 7-Zip Extract",
        "voice": (
            "Here's the new trick in 1.3: 7-Zip control. If a big extraction is hammering "
            "the disk and you need to ease off for a bit, click Refresh 7-Zip, pick the "
            "process it finds, and hit Pause 7-Zip. When you're ready, click Resume. "
            "It simply suspends and wakes the process back up — it never cancels your "
            "extraction."
        ),
    },
    {
        "title": "Example Workflows",
        "voice": (
            "Let's make it concrete with three quick examples. For a backup drive, use "
            "size mode and set it to a hundred gigabytes. For a USB stick, percent mode "
            "at ten percent works nicely. And for a big archive extraction, watch the "
            "target drive and pause 7-Zip if space gets tight. One tip: if 7-Zip was "
            "started as administrator, run this app as administrator too."
        ),
    },
    {
        "title": "Where to Find the Files",
        "voice": (
            "Last stop — where everything lives. The source file is "
            "disk_space_monitor_v1_3.py. The ready-to-run program is in the dist folder, "
            "as DiskSpaceMonitor_v1_3.exe. And the README covers setup, building, usage, "
            "and troubleshooting. That's the full tour of Disk Space Monitor 1.3. "
            "Thanks for watching!"
        ),
    },
]

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = "-4%"

PROJECT_ROOT = Path(__file__).resolve().parent
MEDIA = PROJECT_ROOT / "media"
SLIDE_DIR = MEDIA / "slides"
AUDIO_DIR = MEDIA / "audio"
SEGMENT_DIR = MEDIA / "segments"
OUTPUT = MEDIA / "DiskSpaceMonitor_v1_3_feature_walkthrough_natural.mp4"
CONCAT_LIST = MEDIA / "concat_list_natural.txt"
TRANSCRIPT = MEDIA / "DiskSpaceMonitor_v1_3_voiceover_transcript_natural.txt"


def ensure_edge_tts():
    try:
        import edge_tts  # noqa: F401
        return
    except ImportError:
        pass
    print("The 'edge-tts' package isn't installed.")
    answer = input("Install it now with pip? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts"], check=True)
    else:
        print("Cannot continue without edge-tts. Exiting.")
        sys.exit(1)


def ensure_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg was not found on your PATH.")
        print("Install it from https://www.gyan.dev/ffmpeg/builds/ and try again.")
        sys.exit(1)


TAIL_PAD_SECONDS = 0.4  # short pause held on each slide after the narration ends


async def synth_slide(voice, rate, text, out_path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(out_path))


def audio_duration(path):
    out = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ], check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


async def list_voices():
    import edge_tts
    voices = await edge_tts.list_voices()
    for v in sorted(voices, key=lambda x: x["ShortName"]):
        if v["ShortName"].startswith("en-"):
            print(f"{v['ShortName']:28} {v['Gender']:8} {v.get('FriendlyName', '')}")


def build():
    parser = argparse.ArgumentParser(description="Build a natural neural voiceover video.")
    parser.add_argument("--voice", default=DEFAULT_VOICE,
                        help="edge-tts voice short name. Default: " + DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE,
                        help="speaking rate like -8pct or +5pct (use a percent sign). "
                             "Default: " + DEFAULT_RATE.replace("%", " percent"))
    parser.add_argument("--list-voices", action="store_true",
                        help="list available English voices and exit")
    args = parser.parse_args()

    ensure_edge_tts()

    if args.list_voices:
        asyncio.run(list_voices())
        return

    ensure_ffmpeg()

    for d in (AUDIO_DIR, SEGMENT_DIR):
        d.mkdir(parents=True, exist_ok=True)

    if not SLIDE_DIR.exists():
        print(f"ERROR: slide folder not found: {SLIDE_DIR}")
        print("Run create_voiceover_video.ps1 once to generate the slide images first.")
        sys.exit(1)

    concat_lines = []
    transcript_lines = []

    for i, slide in enumerate(SLIDES, start=1):
        slide_png = SLIDE_DIR / f"slide_{i:02d}.png"
        audio_mp3 = AUDIO_DIR / f"voice_{i:02d}.mp3"
        segment_mp4 = SEGMENT_DIR / f"segment_{i:02d}_natural.mp4"

        if not slide_png.exists():
            print(f"ERROR: missing slide image {slide_png}")
            sys.exit(1)

        print(f"[{i}/{len(SLIDES)}] Synthesizing narration -> {audio_mp3.name}")
        asyncio.run(synth_slide(args.voice, args.rate, slide["voice"], audio_mp3))

        # Hold the slide for exactly the narration length plus a short tail pause.
        # (-shortest alone overshoots with looped still images, leaving a freeze.)
        target = audio_duration(audio_mp3) + TAIL_PAD_SECONDS

        print(f"[{i}/{len(SLIDES)}] Rendering segment -> {segment_mp4.name}")
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(slide_png),
            "-i", str(audio_mp3),
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{target:.3f}",
            "-af", "apad",
            "-vf", "fps=30,format=yuv420p",
            str(segment_mp4),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        concat_lines.append(f"file '{segment_mp4.as_posix()}'")
        transcript_lines.append(f"Slide {i} - {slide['title']}")
        transcript_lines.append(slide["voice"])
        transcript_lines.append("")

    CONCAT_LIST.write_text("\n".join(concat_lines) + "\n", encoding="ascii")
    TRANSCRIPT.write_text("\n".join(transcript_lines), encoding="utf-8")

    print("Concatenating segments -> final video")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(CONCAT_LIST),
        "-c", "copy",
        str(OUTPUT),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print()
    print(f"Done. Voice: {args.voice} (rate {args.rate})")
    print(f"Video:      {OUTPUT}")
    print(f"Transcript: {TRANSCRIPT}")


if __name__ == "__main__":
    build()
