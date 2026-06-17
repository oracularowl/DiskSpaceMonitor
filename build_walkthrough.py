#!/usr/bin/env python3
"""
build_walkthrough.py  —  Disk Space Monitor v1.3 feature walkthrough.

Modern dark/tech motion-graphics walkthrough with a natural neural voice (Guy).
Builds everything from code: SVG scenes -> PNG (cairosvg) -> per-scene clips with
Ken Burns motion (ffmpeg) -> narrated, crossfaded MP4.

USAGE
  python build_walkthrough.py                 # full build with Guy neural voice
  python build_walkthrough.py --voice en-US-JennyNeural
  python build_walkthrough.py --silent        # render visuals only (no TTS needed)

REQUIREMENTS
  pip install cairosvg edge-tts        (edge-tts only needed unless --silent)
  ffmpeg on PATH
  Internet while running (neural voice is synthesized online; free, no key).
"""
import argparse
import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scenes import *  # design tokens + components

OUT = Path(__file__).resolve().parent
WALK = OUT / "media" / "walkthrough"
FRAMES = WALK / "frames"
AUDIO = WALK / "narration"
CLIPS = WALK / "clips"
FINAL = WALK / "DiskSpaceMonitor_v1_3_walkthrough.mp4"

FPS = 30
TRANSITION = 0.7  # crossfade seconds


# ===========================================================================
# SCENES
# ===========================================================================
def s_intro():
    b = [background()]
    b.append(kicker(150, 320, "WINDOWS DESKTOP UTILITY"))
    b.append(text(146, 452, "Disk Space", 92, INK, "bold"))
    b.append(text(146, 556, "Monitor", 92, INK, "bold"))
    b.append('<rect x="150" y="588" width="260" height="6" rx="3" fill="url(#accentbar)"/>')
    b.append(text(150, 656, "Keep an eye on free space — and never", 32, MUT))
    b.append(text(150, 700, "get caught by a full drive again.", 32, MUT))
    c, _ = chip(150, 752, "Version 1.3  ·  Feature Walkthrough", ACCENT)
    b.append(c)
    win, _ = app_window(1150, 150, w=720)
    b.append(win)
    return svg_wrap("".join(b))


def s_overview():
    b = [background()]
    b.append(kicker(150, 150, "EVERYTHING IT DOES"))
    b.append(text(146, 250, "Ten features, one tiny window", 64, INK, "bold"))
    feats = [
        ("Drive selection", "Watch C:, D:, USB — any drive", CYAN),
        ("Two threshold modes", "Alert by percent free or GB free", ACCENT),
        ("Live status panel", "Auto-refreshes every 5 seconds", VIOLET),
        ("Usage at a glance", "Total, used, free + progress bar", CYAN),
        ("Foreground popup alerts", "Jumps to the front when space is low", AMBER),
        ("Start / Stop monitoring", "Timed checks on your interval", ACCENT),
        ("Check Now", "Test the threshold instantly", VIOLET),
        ("7-Zip detection", "Finds running extract jobs", CYAN),
        ("Pause / Resume 7-Zip", "Suspend heavy I/O without cancelling", AMBER),
        ("Standalone EXE", "No Python needed — versioned builds", ACCENT),
    ]
    x0, y0, cw, ch, gx, gy = 150, 330, 790, 132, 40, 26
    for i, (t, d, col) in enumerate(feats):
        x = x0 + (i % 2) * (cw + gx)
        y = y0 + (i // 2) * (ch + gy)
        b.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="16" fill="{PANEL}" stroke="{BORDER}"/>')
        b.append(f'<rect x="{x}" y="{y+18}" width="5" height="{ch-36}" rx="2.5" fill="{col}"/>')
        b.append(f'<circle cx="{x+58}" cy="{y+66}" r="26" fill="{col}" fill-opacity="0.14" stroke="{col}" stroke-opacity="0.5"/>')
        b.append(f'<path d="M{x+46} {y+66} l8 9 l16 -18" stroke="{col}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        b.append(text(x + 102, y + 56, t, 27, INK, "bold"))
        b.append(text(x + 102, y + 92, d, 19, MUT))
    return svg_wrap("".join(b))


def s_app_tour():
    b = [background()]
    b.append(kicker(120, 110, "THE WHOLE APP"))
    b.append(text(116, 196, "One window, four sections", 56, INK, "bold"))
    win, _ = app_window(120, 250, w=720)
    b.append(win)
    b.append(callout(960, 300, "1 · Monitor Settings",
                     ["Pick the drive, the threshold", "mode, and how often to check."],
                     CYAN, point=(840, 430), wbox=440))
    b.append(callout(960, 540, "2 · Current Disk Status",
                     ["Total, used and free space, with", "a live YES / NO threshold flag."],
                     ACCENT, point=(840, 690), wbox=440))
    b.append(callout(960, 780, "3 · Controls + 4 · 7-Zip",
                     ["Start, stop, check now — plus", "pause and resume 7-Zip jobs."],
                     VIOLET, point=(840, 980), wbox=440))
    return svg_wrap("".join(b))


def s_disk():
    b = [background()]
    b.append(kicker(120, 110, "STEP 1 · CHOOSE A DRIVE"))
    b.append(text(116, 196, "Point it at any drive", 56, INK, "bold"))
    win, _ = app_window(120, 250, w=720, highlight="disk")
    b.append(win)
    b.append(callout(960, 330, "The drive dropdown",
                     ["Every Windows drive shows up —", "C:, D:, even a USB stick."],
                     CYAN, point=(560, 410), wbox=470))
    b.append(callout(960, 560, "Refresh Disks",
                     ["Plugged something in just now?", "One click re-scans your drives."],
                     ACCENT, point=(760, 410), wbox=470))
    b.append(callout(960, 790, "Instant read-out",
                     ["Total, used and free space appear", "the moment a drive is selected."],
                     VIOLET, point=(700, 690), wbox=470))
    return svg_wrap("".join(b))


def s_threshold():
    b = [background()]
    b.append(kicker(150, 130, "STEP 2 · SET THE LINE"))
    b.append(text(146, 216, "Two ways to say “too full”", 56, INK, "bold"))
    cards = [
        ("Percent free", CYAN, "Alert when free space drops below a percentage.",
         "“Warn me at 10% free.”", "Great for everyday monitoring of any drive size."),
        ("Size free (GB)", VIOLET, "Alert when free space drops below an amount.",
         "“Warn me at 100 GB free.”", "Perfect when you need a fixed amount of working room."),
    ]
    for i, (t, col, d, ex, note) in enumerate(cards):
        x = 150 + i * 840
        y = 330
        b.append(f'<rect x="{x}" y="{y}" width="770" height="470" rx="20" fill="{PANEL}" stroke="{col}" stroke-opacity="0.5"/>')
        b.append(f'<rect x="{x}" y="{y}" width="770" height="8" rx="4" fill="{col}"/>')
        b.append(f'<circle cx="{x+70}" cy="{y+96}" r="34" fill="{col}" fill-opacity="0.14" stroke="{col}"/>')
        sym = "%" if i == 0 else "GB"
        b.append(text(x + 70, y + 108, sym, 30 if i == 0 else 22, col, "bold", anchor="middle"))
        b.append(text(x + 130, y + 92, t, 38, INK, "bold"))
        b.append(text(x + 130, y + 128, "Threshold mode", 20, MUT))
        b.append(text(x + 44, y + 210, d, 24, INK))
        b.append(f'<rect x="{x+44}" y="{y+250}" width="682" height="74" rx="12" fill="{col}" fill-opacity="0.10" stroke="{col}" stroke-opacity="0.35"/>')
        b.append(text(x + 70, y + 297, ex, 30, col, "bold", font=MONO))
        b.append(text(x + 44, y + 384, note, 21, MUT))
        b.append(text(x + 44, y + 416, "", 21, MUT))
    return svg_wrap("".join(b))


def s_status():
    b = [background()]
    b.append(kicker(120, 120, "STEP 3 · READ THE STATUS"))
    b.append(text(116, 206, "Live status, no clicking required", 54, INK, "bold"))
    panel, ph = big_status(120, 300, w=900)
    b.append(panel)
    b.append(callout(1110, 330, "Auto-refresh",
                     ["The panel updates itself every", "five seconds — even when alerts", "are switched off."],
                     ACCENT, point=(1020, 360), wbox=460))
    b.append(callout(1110, 560, "Threshold reached",
                     ["The line to watch. YES means the", "drive is already at or below your", "limit. NO means you're fine."],
                     RED, point=(700, 560), wbox=460))
    b.append(callout(1110, 800, "Usage bar",
                     ["A quick visual of how full the", "drive is right now."],
                     CYAN, point=(700, 690), wbox=460))
    return svg_wrap("".join(b))


def s_monitor():
    b = [background()]
    b.append(kicker(120, 110, "STEP 4 · TURN ON ALERTS"))
    b.append(text(116, 196, "Start Monitoring — then relax", 54, INK, "bold"))
    win, _ = app_window(120, 250, w=720, highlight="start")
    b.append(win)
    b.append(callout(960, 320, "Start / Stop",
                     ["Start Monitoring begins timed", "checks. Stop ends them anytime."],
                     ACCENT, point=(300, 838), wbox=470))
    b.append(callout(960, 540, "Your interval",
                     ["“Check every (s)” sets the rhythm —", "every 30 seconds, for example."],
                     CYAN, point=(700, 560), wbox=470))
    b.append(callout(960, 760, "Check Now",
                     ["Want to test it? Set percent to 100", "and click Check Now — the alert", "fires instantly."],
                     VIOLET, point=(620, 838), wbox=470))
    return svg_wrap("".join(b))


def s_popup():
    b = [background()]
    b.append(kicker(120, 110, "THE ALERT"))
    b.append(text(116, 196, "It comes to you", 56, INK, "bold"))
    win, _ = app_window(120, 250, w=720, dim=True)
    b.append(win)
    b.append(alert_window(720, 640, w=600, h=340))
    b.append(callout(1140, 360, "Foreground popup",
                     ["When the threshold is hit, a topmost", "window jumps to the front — so you", "won't miss it behind other apps."],
                     AMBER, point=(900, 560), wbox=520))
    b.append(callout(1140, 700, "Clear details",
                     ["It shows the drive, the exact free", "space, and the threshold you set."],
                     ACCENT, point=(900, 700), wbox=520))
    return svg_wrap("".join(b))


def s_sevenzip():
    b = [background()]
    b.append(kicker(120, 110, "NEW IN 1.3 · 7-ZIP CONTROL"))
    b.append(text(116, 196, "Pause a heavy extraction", 54, INK, "bold"))
    win, _ = app_window(120, 250, w=720, highlight="sevenzip", sevenzip_state="paused")
    b.append(win)
    b.append(callout(960, 320, "Detects running jobs",
                     ["Refresh 7-Zip finds active extract", "processes: 7z, 7za, 7zr and 7zG."],
                     CYAN, point=(560, 838), wbox=480))
    b.append(callout(960, 545, "Pause / Resume",
                     ["Suspend a job to free up disk I/O,", "then resume right where it left off."],
                     AMBER, point=(560, 900), wbox=480))
    b.append(callout(960, 770, "It never cancels",
                     ["Pausing only suspends the process —", "your extraction is never lost.", "(Run as admin for elevated jobs.)"],
                     ACCENT, point=(700, 960), wbox=480))
    return svg_wrap("".join(b))


def s_workflows():
    b = [background()]
    b.append(kicker(150, 130, "PUT IT TOGETHER"))
    b.append(text(146, 216, "Three real-world setups", 56, INK, "bold"))
    cards = [
        ("Backup drive", CYAN, "SIZE", "100 GB",
         ["Use size mode.", "Alert at 100 GB free so", "backups never run dry."]),
        ("USB stick", VIOLET, "PERCENT", "10%",
         ["Use percent mode.", "Alert at 10% free —", "size-independent."]),
        ("Big extraction", AMBER, "7-ZIP", "Pause",
         ["Watch the target drive.", "Pause 7-Zip if free", "space gets tight."]),
    ]
    for i, (t, col, tag, big, lines) in enumerate(cards):
        x = 150 + i * 545
        y = 330
        b.append(f'<rect x="{x}" y="{y}" width="495" height="470" rx="20" fill="{PANEL}" stroke="{BORDER}"/>')
        b.append(f'<rect x="{x}" y="{y}" width="495" height="8" rx="4" fill="{col}"/>')
        cc, _ = chip(x + 36, y + 44, tag, col)
        b.append(cc)
        b.append(text(x + 36, y + 168, t, 36, INK, "bold"))
        b.append(text(x + 36, y + 258, big, 64, col, "bold"))
        for j, ln in enumerate(lines):
            b.append(text(x + 36, y + 330 + j * 40, ln, 22, MUT))
    return svg_wrap("".join(b))


def s_outro():
    b = [background()]
    b.append(kicker(150, 230, "WHERE EVERYTHING LIVES"))
    b.append(text(146, 330, "Ready when you are", 70, INK, "bold"))
    rows = [
        ("Source", "disk_space_monitor_v1_3.py", CYAN),
        ("Executable", "dist / DiskSpaceMonitor_v1_3.exe", ACCENT),
        ("Docs", "README.md — setup, build, troubleshooting", VIOLET),
    ]
    for i, (k, v, col) in enumerate(rows):
        y = 430 + i * 92
        b.append(f'<rect x="150" y="{y}" width="980" height="72" rx="14" fill="{PANEL}" stroke="{BORDER}"/>')
        b.append(f'<rect x="150" y="{y}" width="6" height="72" rx="3" fill="{col}"/>')
        b.append(text(186, y + 46, k, 24, col, "bold"))
        b.append(text(400, y + 46, v, 24, INK, font=MONO))
    b.append(text(150, 820, "That's Disk Space Monitor 1.3 — thanks for watching.", 30, MUT))
    win, _ = app_window(1230, 170, w=560)
    b.append(f'<g opacity="0.96">{win}</g>')
    return svg_wrap("".join(b))


SCENES = [
    ("intro", s_intro,
     "Meet Disk Space Monitor, version one point three. It's a small Windows app "
     "with one job: keep an eye on your free disk space, and tap you on the shoulder "
     "before a drive fills up. Let's take the full tour."),
    ("overview", s_overview,
     "Don't let the size fool you. Packed into this one little window are ten features — "
     "drive selection, two kinds of alerts, a live status panel, foreground pop-ups, "
     "timed monitoring, and brand-new in this version, 7-Zip controls. Here's how they all fit together."),
    ("app_tour", s_app_tour,
     "The whole app is a single window, split into four parts. Up top, Monitor Settings, "
     "where you choose what to watch. In the middle, Current Disk Status. Then your control "
     "buttons. And down at the bottom, the new 7-Zip section. Let's walk through each one."),
    ("disk", s_disk,
     "First, point it at a drive. The dropdown lists every drive Windows can see — your C "
     "drive, a D drive, an external USB stick, whatever's plugged in. Added a drive just now? "
     "Hit Refresh Disks and it shows up. The moment you pick one, its total, used, and free "
     "space appear."),
    ("threshold", s_threshold,
     "Next, tell it what counts as too full — and you get two ways to do that. Percent mode "
     "says, warn me at ten percent free; great for everyday monitoring. Size mode says, warn "
     "me at a hundred gigabytes free; perfect when you need a fixed amount of room. Pick "
     "whichever fits the drive."),
    ("status", s_status,
     "Now the part you'll actually glance at. The status panel refreshes itself every five "
     "seconds — no clicking. The line to watch is Threshold reached. Yes means you're at or "
     "below your limit; no means you're fine. And the bar gives you the whole picture at a glance."),
    ("monitor", s_monitor,
     "To turn on alerts, click Start Monitoring. From there it checks the drive on your "
     "schedule — say every thirty seconds — and Stop ends it whenever you like. Want to prove "
     "it works right now? Set percent to a hundred and hit Check Now. The alert fires instantly."),
    ("popup", s_popup,
     "And when that threshold is crossed, the alert comes to you. A topmost pop-up jumps to "
     "the front, right over whatever you're doing, so it's impossible to miss. It spells out "
     "the drive, exactly how much space is left, and the threshold you set."),
    ("sevenzip", s_sevenzip,
     "Here's the headline feature in one point three: 7-Zip control. If a big extraction is "
     "hammering your disk, click Refresh 7-Zip, pick the job, and Pause it to free up the drive. "
     "Resume picks up right where it left off. And don't worry — pausing only suspends it. Your "
     "extraction is never cancelled."),
    ("workflows", s_workflows,
     "So how do people actually use it? Three quick setups. For a backup drive, size mode at a "
     "hundred gigabytes. For a USB stick, percent mode at ten percent. And for a giant extraction, "
     "watch the target drive and pause 7-Zip if things get tight."),
    ("outro", s_outro,
     "And that's the whole tour. The Python source, a standalone executable that needs no "
     "install, and a full README are all in the project folder. That's Disk Space Monitor, "
     "version one point three — thanks for watching."),
]


# ===========================================================================
# PIPELINE
# ===========================================================================
def render_frames(force=False):
    WALK.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(exist_ok=True)
    have = all((FRAMES / f"{n}.png").exists() for n, _, _ in SCENES)
    if have and not force:
        print(f"Using {len(SCENES)} pre-rendered scenes in {FRAMES}")
        return
    import cairosvg  # only needed when (re)rendering the SVG scenes
    for name, fn, _ in SCENES:
        svg = fn()
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(FRAMES / f"{name}.png"),
                         output_width=W, output_height=H)
    print(f"Rendered {len(SCENES)} scenes -> {FRAMES}")


async def _synth(voice, text, path):
    import edge_tts
    await edge_tts.Communicate(text, voice=voice, rate="-3%").save(str(path))


def synth_audio(voice):
    AUDIO.mkdir(exist_ok=True)
    for name, _, narration in SCENES:
        asyncio.run(_synth(voice, narration, AUDIO / f"{name}.mp3"))
    print(f"Synthesized narration -> {AUDIO}")


def media_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def estimate_duration(text):
    return max(4.0, len(text.split()) / 2.5 + 1.0)


def make_clip(name, duration, idx):
    """Fast static clip (image + optional audio). Motion comes from crossfades."""
    png = FRAMES / f"{name}.png"
    mp3 = AUDIO / f"{name}.mp3"
    clip = CLIPS / f"{idx:02d}_{name}.mp4"
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(png)]
    if mp3.exists():
        cmd += ["-i", str(mp3)]
    cmd += ["-t", f"{duration:.3f}",
            "-vf", f"fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
            "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if mp3.exists():
        cmd += ["-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest"]
    else:
        cmd += ["-an"]
    cmd += [str(clip)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return clip


def assemble(clips, durations):
    """Crossfade clips together (video) with matching audio crossfades."""
    have_audio = (AUDIO / f"{SCENES[0][0]}.mp3").exists()
    inputs = []
    for c in clips:
        inputs += ["-i", str(c)]
    # build xfade chain
    vlabels = [f"[{i}:v]" for i in range(len(clips))]
    filt = []
    prev = vlabels[0]
    offset = 0.0
    for i in range(1, len(clips)):
        offset += durations[i - 1] - TRANSITION
        out = f"[v{i}]"
        filt.append(f"{prev}{vlabels[i]}xfade=transition=fade:duration={TRANSITION}:offset={offset:.3f}{out}")
        prev = out
    vchain = ";".join(filt)
    final_v = prev
    fc = vchain
    if have_audio:
        prevA = "[0:a]"
        afilt = []
        for i in range(1, len(clips)):
            out = f"[a{i}]"
            afilt.append(f"{prevA}[{i}:a]acrossfade=d={TRANSITION}{out}")
            prevA = out
        fc = vchain + ";" + ";".join(afilt)
        final_a = prevA
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", fc, "-map", final_v]
    if have_audio:
        cmd += ["-map", final_a, "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS), str(FINAL)]
    subprocess.run(cmd, check=True)


def build(voice, silent):
    if shutil.which("ffmpeg") is None:
        sys.exit("ERROR: ffmpeg not found on PATH.")
    render_frames()
    if not silent:
        synth_audio(voice)
    for d in (CLIPS,):
        d.mkdir(exist_ok=True)
    clips, durations = [], []
    for idx, (name, _, narration) in enumerate(SCENES):
        mp3 = AUDIO / f"{name}.mp3"
        dur = (media_duration(mp3) + 0.6) if mp3.exists() else estimate_duration(narration)
        durations.append(dur)
        clips.append(make_clip(name, dur, idx))
        print(f"  clip {idx+1}/{len(SCENES)}: {name}  ({dur:.1f}s)")
    assemble(clips, durations)
    total = sum(durations) - TRANSITION * (len(clips) - 1)
    print(f"\nDone -> {FINAL}  (~{total:.0f}s, voice={'silent' if silent else voice})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en-US-GuyNeural")
    ap.add_argument("--silent", action="store_true")
    ap.add_argument("--render-frames", action="store_true", help="re-render scene PNGs from SVG (needs cairosvg)")
    a = ap.parse_args()
    if a.render_frames:
        render_frames(force=True)
    build(a.voice, a.silent)
