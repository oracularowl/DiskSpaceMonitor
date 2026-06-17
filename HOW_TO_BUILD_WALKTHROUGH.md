# Disk Space Monitor — feature walkthrough video

A modern dark/tech motion-graphics walkthrough that covers every feature, with
pixel-faithful recreations of the app's screens, callouts, crossfade transitions,
and a natural neural narration (Microsoft "Guy" voice).

## What's in the box

```
build_walkthrough.py                      the builder
scenes.py                                 the scene/UI designs (vector)
media/walkthrough/frames/*.png            11 pre-rendered 1080p scenes
media/walkthrough/walkthrough_preview_silent.mp4   silent preview of the flow
```

The 11 scenes: intro · feature overview · app tour · choose a drive · threshold
modes · live status · start monitoring · the popup alert · 7-Zip pause/resume ·
example workflows · where the files live.

## Build the final video (with the Guy voice)

The scenes are already rendered, so you only need two tools — no cairosvg:

1. **ffmpeg** on PATH — https://www.gyan.dev/ffmpeg/builds/
2. **edge-tts**:
   ```powershell
   python -m pip install edge-tts
   ```

Then, from the project folder:

```powershell
python build_walkthrough.py
```

Output: `media/walkthrough/DiskSpaceMonitor_v1_3_walkthrough.mp4`

> Internet is required while it runs — the neural voice is synthesized by
> Microsoft's free service (no key, no account). This is why the final voiced
> video builds on your PC and not inside the Claude sandbox, where that endpoint
> is blocked.

## Options

```powershell
python build_walkthrough.py --voice en-US-AriaNeural   # warm female
python build_walkthrough.py --voice en-US-JennyNeural  # clear female
python build_walkthrough.py --voice en-GB-RyanNeural   # British male
python build_walkthrough.py --silent                   # no narration (no edge-tts needed)
python build_walkthrough.py --render-frames            # re-render scene art (needs: pip install cairosvg)
```

## Want to change the visuals or wording?

- **Narration** lives in the `SCENES` list in `build_walkthrough.py` (one entry
  per scene). Edit the text and rebuild.
- **Scene art** is vector code in `scenes.py` + the `s_*()` builders in
  `build_walkthrough.py`. After editing, re-render with `--render-frames`
  (that step needs `pip install cairosvg`).
- Timing is automatic — each scene is held for exactly its narration length, so
  you never have to line anything up by hand.

## Notes

- The screens are faithful **recreations** of the real app (same sections,
  labels, status read-out, 7-Zip panel), styled to match the video. They are not
  screen captures of the live program — capturing the real Windows app would need
  a recording on your machine; say the word and I'll set that up instead.
- The silent preview shows the visual flow and transitions. The real build adds
  the voice and paces each scene to it.
