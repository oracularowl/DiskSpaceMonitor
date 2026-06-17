#!/usr/bin/env python3
"""Scene SVG builders for the Disk Space Monitor walkthrough (modern dark/tech)."""

W, H = 1920, 1080

BG0, BG1 = "#060a14", "#0a1322"
PANEL = "#0f1a2e"
PANEL2 = "#13203a"
BORDER = "#243456"
ACCENT = "#5eead4"
CYAN = "#38bdf8"
VIOLET = "#a78bfa"
AMBER = "#fbbf24"
RED = "#fb7185"
GREEN = "#34d399"
INK = "#eaf1ff"
MUT = "#8aa0c6"
FAINT = "#5b6f96"
SANS = "DejaVu Sans"
MONO = "DejaVu Sans Mono"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def background(grid=True, glow=True):
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    if glow:
        s.append('<rect width="%d" height="%d" fill="url(#glowA)"/>' % (W, H))
        s.append('<rect width="%d" height="%d" fill="url(#glowB)"/>' % (W, H))
    if grid:
        s.append('<rect width="%d" height="%d" fill="url(#grid)"/>' % (W, H))
    return "".join(s)


def defs():
    return f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/>
</linearGradient>
<radialGradient id="glowA" cx="0.16" cy="0.12" r="0.7">
  <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.16"/>
  <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowB" cx="0.9" cy="0.95" r="0.8">
  <stop offset="0" stop-color="{VIOLET}" stop-opacity="0.14"/>
  <stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/>
</radialGradient>
<pattern id="grid" width="46" height="46" patternUnits="userSpaceOnUse">
  <path d="M46 0H0V46" fill="none" stroke="#13203a" stroke-width="1"/>
</pattern>
<linearGradient id="accentbar" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{CYAN}"/>
</linearGradient>
<linearGradient id="titlebar" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#16233f"/><stop offset="1" stop-color="#101a30"/>
</linearGradient>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="18" stdDeviation="26" flood-color="#000000" flood-opacity="0.55"/>
</filter>
<filter id="glowtxt" x="-50%" y="-50%" width="200%" height="200%">
  <feDropShadow dx="0" dy="0" stdDeviation="10" flood-color="{ACCENT}" flood-opacity="0.55"/>
</filter>
</defs>'''


def text(x, y, s, size=28, fill=INK, weight="normal", font=SANS, anchor="start",
         spacing=None, opacity=1):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"{sp} '
            f'opacity="{opacity}">{esc(s)}</text>')


def chip(x, y, label, color=ACCENT):
    w = 26 + len(label) * 13
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="46" rx="23" '
            f'fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-opacity="0.5"/>'
            f'{text(x + 22, y + 31, label, 23, color, "bold")}</g>'), w


def kicker(x, y, label, color=ACCENT):
    return (f'<g>{text(x, y, label, 24, color, "bold", spacing="4")}'
            f'<rect x="{x}" y="{y+14}" width="64" height="4" rx="2" fill="url(#accentbar)"/></g>')


def app_window(x, y, w=720, dim=False, highlight=None, sevenzip_state="idle",
               status_kind="normal"):
    h = 880
    op = 0.4 if dim else 1.0
    g = [f'<g opacity="{op}" filter="url(#soft)">']
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{PANEL}" stroke="{BORDER}"/>')
    g.append(f'<path d="M{x} {y+14} q0 -14 14 -14 h{w-28} q14 0 14 14 v34 h-{w} z" fill="url(#titlebar)"/>')
    g.append(f'<circle cx="{x+26}" cy="{y+24}" r="9" fill="{ACCENT}"/>')
    g.append(f'<path d="M{x+21} {y+24} l4 4 l7 -8" stroke="{BG0}" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    g.append(text(x + 48, y + 31, "Disk Space Monitor v1.3", 21, INK, "bold"))
    bx = x + w - 96
    for i, col in enumerate([MUT, MUT, RED]):
        g.append(f'<circle cx="{bx + i*30}" cy="{y+24}" r="6.5" fill="{col}" fill-opacity="0.85"/>')
    pad = x + 26
    cw = w - 52
    cy = y + 70
    g.append(text(pad, cy + 8, "Monitor a selected disk and pop up a foreground alert when free space is low.", 17, MUT))
    cy += 34

    def section(title, sy, sh, hl):
        stroke = ACCENT if hl else BORDER
        sw = 3 if hl else 1
        glow = ' filter="url(#glowtxt)"' if hl else ''
        return (f'<rect x="{pad}" y="{sy}" width="{cw}" height="{sh}" rx="11" '
                f'fill="{PANEL2}" stroke="{stroke}" stroke-width="{sw}"{glow}/>'
                f'<rect x="{pad+20}" y="{sy-12}" width="{28+len(title)*9.2:.0f}" height="24" rx="6" fill="{PANEL}"/>'
                f'{text(pad+30, sy+5, title, 16, ACCENT if hl else MUT, "bold")}')

    g.append(section("Monitor Settings", cy, 168, highlight in ("settings", "disk", "threshold")))
    g.append(text(pad + 24, cy + 44, "Disk to monitor", 17, INK))
    g.append(_combo(pad + 200, cy + 26, 210, "A:\\", open_=(highlight == "disk")))
    g.append(_btn(pad + 430, cy + 26, 150, "Refresh Disks", outline=True))
    g.append(text(pad + 24, cy + 92, "Threshold type", 17, INK))
    g.append(_radio(pad + 200, cy + 78, "Percent free", on=(status_kind != "size")))
    g.append(_radio(pad + 360, cy + 78, "Size free (GB)", on=(status_kind == "size")))
    g.append(text(pad + 24, cy + 147, "Threshold value", 17, INK))
    g.append(_field(pad + 200, cy + 124, 150, "10"))
    g.append(text(pad + 372, cy + 147, "Check every (s)", 15, MUT))
    g.append(_field(pad + 520, cy + 124, 80, "30"))
    cy += 168 + 28

    g.append(section("Current Disk Status", cy, 250, highlight == "status"))
    lines = _status_lines(status_kind)
    ly = cy + 40
    for ln, col in lines:
        g.append(text(pad + 24, ly, ln, 18, col, font=MONO))
        ly += 27
    pct = 0.97 if status_kind != "low" else 0.62
    g.append(f'<rect x="{pad+24}" y="{cy+218}" width="{cw-48}" height="16" rx="8" fill="#0a1424" stroke="{BORDER}"/>')
    barcol = RED if pct > 0.9 else CYAN
    g.append(f'<rect x="{pad+24}" y="{cy+218}" width="{(cw-48)*pct:.0f}" height="16" rx="8" fill="{barcol}"/>')
    cy += 250 + 26

    g.append(_btn(pad, cy, 190, "Start Monitoring", primary=True, hl=(highlight == "start")))
    g.append(_btn(pad + 206, cy, 170, "Stop Monitoring", outline=True))
    g.append(_btn(pad + 392, cy, 150, "Check Now", outline=True, hl=(highlight == "check")))
    g.append(_btn(pad + cw - 90, cy, 90, "Quit", outline=True))
    cy += 74

    hl7 = highlight == "sevenzip"
    g.append(section("7-Zip Extract Process", cy, 150, hl7))
    g.append(text(pad + 24, cy + 44, "Running 7-Zip process", 17, INK))
    sevenval = "7zG.exe - PID 8124" if sevenzip_state != "none" else ""
    g.append(_combo(pad + 250, cy + 26, 240, sevenval, open_=False))
    g.append(_btn(pad + 510, cy + 26, 150, "Refresh 7-Zip", outline=True))
    g.append(_btn(pad + 250, cy + 78, 130, "Pause 7-Zip", outline=True, hl=(sevenzip_state == "paused")))
    g.append(_btn(pad + 392, cy + 78, 140, "Resume 7-Zip", outline=True, hl=(sevenzip_state == "resumed")))
    msg = {"idle": "Found 1 running 7-Zip process.",
           "paused": "Paused 7zG.exe - PID 8124. Click Resume 7-Zip to continue it.",
           "resumed": "Resumed 7zG.exe - PID 8124.",
           "none": "No running 7-Zip process found. Start an extraction, then Refresh."}[sevenzip_state]
    mcol = AMBER if sevenzip_state == "paused" else (GREEN if sevenzip_state == "resumed" else MUT)
    g.append(text(pad + 24, cy + 128, msg, 14.5, mcol, font=MONO))
    g.append('</g>')
    return "".join(g), (x, y, w, h)


def _status_lines(kind):
    if kind == "size":
        return [("Disk:  D:\\", INK), ("Total: 931.51 GB", MUT),
                ("Used:  860.00 GB (92.32%)", MUT),
                ("Free:  71.51 GB (7.68%)", INK),
                ("Alert threshold: 100.00 GB free", INK),
                ("Threshold reached: YES", RED),
                ("Popup monitoring: ON", CYAN)]
    return [("Disk:  A:\\", INK), ("Total: 4.55 TB", MUT),
            ("Used:  4.41 TB (97.00%)", MUT),
            ("Free:  139.62 GB (3.00%)", INK),
            ("Alert threshold: 10.00% free", INK),
            ("Threshold reached: YES", RED),
            ("Popup monitoring: OFF", AMBER)]


def _combo(x, y, w, val, open_=False):
    g = [f'<rect x="{x}" y="{y}" width="{w}" height="40" rx="8" fill="#0b1626" stroke="{ACCENT if open_ else BORDER}" stroke-width="{2 if open_ else 1}"/>']
    g.append(text(x + 14, y + 27, val, 17, INK, font=MONO))
    g.append(f'<path d="M{x+w-26} {y+16} l8 9 l8 -9" stroke="{MUT}" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    if open_:
        opts = ["C:\\", "D:\\", "A:\\"]
        g.append(f'<rect x="{x}" y="{y+44}" width="{w}" height="{len(opts)*38+8}" rx="8" fill="#0c1a2e" stroke="{ACCENT}" filter="url(#soft)"/>')
        for i, o in enumerate(opts):
            oy = y + 52 + i * 38
            if o == val:
                g.append(f'<rect x="{x+5}" y="{oy-22}" width="{w-10}" height="34" rx="6" fill="{ACCENT}" fill-opacity="0.16"/>')
            g.append(text(x + 14, oy, o, 17, ACCENT if o == val else INK, font=MONO))
    return "".join(g)


def _btn(x, y, w, label, primary=False, outline=False, hl=False):
    if primary:
        fill, stroke, tc = "url(#accentbar)", "none", BG0
    elif outline:
        fill, stroke, tc = "#10203a", BORDER, INK
    else:
        fill, stroke, tc = PANEL2, BORDER, INK
    g = [f'<rect x="{x}" y="{y}" width="{w}" height="40" rx="9" fill="{fill}" stroke="{stroke}"/>']
    if hl:
        g.append(f'<rect x="{x-3}" y="{y-3}" width="{w+6}" height="46" rx="11" fill="none" stroke="{ACCENT}" stroke-width="3" filter="url(#glowtxt)"/>')
    g.append(text(x + w/2, y + 26, label, 16.5, tc, "bold", anchor="middle"))
    return "".join(g)


def _radio(x, y, label, on=False):
    c = ACCENT if on else MUT
    g = [f'<circle cx="{x+11}" cy="{y+12}" r="10" fill="none" stroke="{c}" stroke-width="2"/>']
    if on:
        g.append(f'<circle cx="{x+11}" cy="{y+12}" r="5" fill="{ACCENT}"/>')
    g.append(text(x + 30, y + 18, label, 16.5, INK if on else MUT))
    return "".join(g)


def _field(x, y, w, val):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="40" rx="8" fill="#0b1626" stroke="{BORDER}"/>'
            f'{text(x + 14, y + 27, val, 17, INK, font=MONO)}')


def callout(x, y, title, body, color=ACCENT, point=None, side="left", wbox=420):
    g = ['<g>']
    if point:
        px, py = point
        ax = x if side == "left" else x + wbox
        ay = y + 48
        g.append(f'<line x1="{ax}" y1="{ay}" x2="{px}" y2="{py}" stroke="{color}" stroke-width="2.5" stroke-dasharray="2 7" stroke-linecap="round"/>')
        g.append(f'<circle cx="{px}" cy="{py}" r="7" fill="none" stroke="{color}" stroke-width="2.5"/>')
        g.append(f'<circle cx="{px}" cy="{py}" r="2.5" fill="{color}"/>')
    bh = 40 + 30 * len(body)
    g.append(f'<rect x="{x}" y="{y}" width="{wbox}" height="{bh}" rx="14" fill="{PANEL}" stroke="{color}" stroke-opacity="0.55" filter="url(#soft)"/>')
    g.append(f'<rect x="{x}" y="{y+14}" width="5" height="{bh-28}" rx="2.5" fill="{color}"/>')
    g.append(text(x + 26, y + 38, title, 23, color, "bold"))
    for i, line in enumerate(body):
        g.append(text(x + 26, y + 74 + i * 30, line, 19, INK if i == 0 else MUT))
    g.append('</g>')
    return "".join(g)


def alert_window(cx, cy, w=560, h=320):
    x, y = cx - w // 2, cy - h // 2
    g = ['<g filter="url(#soft)">']
    g.append(f'<rect x="{x-6}" y="{y-6}" width="{w+12}" height="{h+12}" rx="20" fill="none" stroke="{AMBER}" stroke-opacity="0.5" stroke-width="3" filter="url(#glowtxt)"/>')
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{PANEL}" stroke="{BORDER}"/>')
    g.append(f'<path d="M{x} {y+16} q0 -16 16 -16 h{w-32} q16 0 16 16 v34 h-{w} z" fill="url(#titlebar)"/>')
    g.append(text(x + 26, y + 33, "Disk Space Threshold Reached", 19, INK, "bold"))
    g.append(f'<circle cx="{x+w-28}" cy="{y+25}" r="6.5" fill="{RED}" fill-opacity="0.85"/>')
    ix, iy = x + 54, y + 120
    g.append(f'<path d="M{ix} {iy+34} L{ix+34} {iy-26} L{ix+68} {iy+34} Z" fill="{AMBER}" fill-opacity="0.16" stroke="{AMBER}" stroke-width="2.5" stroke-linejoin="round"/>')
    g.append(text(ix + 34, iy + 22, "!", 40, AMBER, "bold", anchor="middle"))
    g.append(text(x + 150, y + 118, "Disk space threshold reached", 23, INK, "bold"))
    g.append(text(x + 150, y + 156, "Disk A:\\ has reached the free-space threshold.", 17, MUT))
    g.append(text(x + 150, y + 190, "Current free space:  139.62 GB (3.00%)", 17, INK, font=MONO))
    g.append(text(x + 150, y + 218, "Threshold:  10.00% free", 17, INK, font=MONO))
    g.append(_btn(x + w/2 - 55, y + h - 64, 110, "OK", primary=True))
    g.append('</g>')
    return "".join(g)


def big_status(x, y, w=820):
    lines = _status_lines("normal")
    h = 56 + len(lines) * 44 + 70
    g = [f'<g filter="url(#soft)">']
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{PANEL2}" stroke="{BORDER}"/>')
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="52" rx="16" fill="{PANEL}"/>')
    g.append(f'<rect x="{x}" y="{y+36}" width="{w}" height="16" fill="{PANEL}"/>')
    g.append(f'<circle cx="{x+28}" cy="{y+26}" r="7" fill="{CYAN}"/>')
    g.append(text(x + 48, y + 33, "Current Disk Status", 19, INK, "bold"))
    g.append(text(x + w - 24, y + 33, "auto-refresh / 5s", 16, ACCENT, anchor="end"))
    ly = y + 92
    for ln, col in lines:
        g.append(text(x + 28, ly, ln, 24, col, font=MONO))
        ly += 44
    g.append(f'<rect x="{x+28}" y="{ly-12}" width="{w-56}" height="18" rx="9" fill="#0a1424" stroke="{BORDER}"/>')
    g.append(f'<rect x="{x+28}" y="{ly-12}" width="{(w-56)*0.97:.0f}" height="18" rx="9" fill="{RED}"/>')
    g.append('</g>')
    return "".join(g), h


def svg_wrap(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">{defs()}{body}</svg>')
