param(
    [string]$VoiceName = "Microsoft Zira Desktop",
    [int]$Rate = 0
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MediaDir = Join-Path $ProjectRoot "media"
$SlideDir = Join-Path $MediaDir "slides"
$AudioDir = Join-Path $MediaDir "audio"
$SegmentDir = Join-Path $MediaDir "segments"
$TranscriptPath = Join-Path $MediaDir "DiskSpaceMonitor_v1_3_voiceover_transcript.txt"
$OutputVideo = Join-Path $MediaDir "DiskSpaceMonitor_v1_3_feature_walkthrough.mp4"
$ConcatList = Join-Path $MediaDir "concat_list.txt"

New-Item -ItemType Directory -Force -Path $MediaDir, $SlideDir, $AudioDir, $SegmentDir | Out-Null

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Speech

$slides = @(
    [pscustomobject]@{
        Title = "Disk Space Monitor v1.3"
        Bullets = @(
            "Windows GUI utility for watching free disk space",
            "Foreground popup alerts when free space is low",
            "Includes 7-Zip pause and resume controls"
        )
        Voice = "This is Disk Space Monitor version 1.3, a small Windows desktop utility for keeping an eye on free disk space. It is built with Python and Tkinter, and it can also control a running Seven Zip extract process. In this walkthrough, we will look at the main features, how to set a threshold, how alerts work, and a few practical examples."
    },
    [pscustomobject]@{
        Title = "Choose the Disk to Monitor"
        Bullets = @(
            "Select any available Windows drive",
            "Use Refresh Disks after plugging in a USB drive",
            "Status shows total, used, and free space"
        )
        Voice = "Start by selecting the disk you want to monitor. The drop down shows available Windows drive letters such as C, D, or a removable USB drive. If you connect a new drive while the app is already open, click Refresh Disks. The status area then shows total space, used space, free space, and the current free space percentage."
    },
    [pscustomobject]@{
        Title = "Set a Free-Space Threshold"
        Bullets = @(
            "Percent mode alerts when free percent is low",
            "GB mode alerts when free GB is low",
            "Example: 10 percent free or 100 GB free"
        )
        Voice = "Next, choose how you want the alert threshold to work. Percent free mode is useful for general monitoring, for example alert me when the drive has ten percent or less free space. Size free mode is useful when you need a specific amount of working room, for example alert me when the drive has one hundred gigabytes or less free."
    },
    [pscustomobject]@{
        Title = "Read the Live Status"
        Bullets = @(
            "Display refreshes automatically every 5 seconds",
            "Threshold reached shows YES or NO",
            "Popup monitoring shows ON or OFF"
        )
        Voice = "The live status area refreshes automatically every five seconds. The most important line is Threshold reached. If it says Yes, the selected drive is already at or below your threshold. Popup monitoring tells you whether alerts are active. This means you can inspect the drive status without turning on popups first."
    },
    [pscustomobject]@{
        Title = "Start Popup Monitoring"
        Bullets = @(
            "Click Start Monitoring to enable alerts",
            "Set the check interval in seconds",
            "Use Check Now to test immediately"
        )
        Voice = "To enable alerts, click Start Monitoring. The app checks the drive at the interval you set, such as every thirty seconds. If the threshold is reached, a foreground popup appears. For a quick test, set Percent free to one hundred and click Check Now or Start Monitoring. Because every drive has one hundred percent or less free space, the alert should trigger immediately."
    },
    [pscustomobject]@{
        Title = "Pause a Running 7-Zip Extract"
        Bullets = @(
            "Click Refresh 7-Zip to find running jobs",
            "Select the 7-Zip process",
            "Pause and resume without terminating the extract"
        )
        Voice = "Version 1.3 also adds Seven Zip process control. If a large extraction is running and you need to temporarily reduce disk activity, click Refresh Seven Zip. Select the detected process, then click Pause Seven Zip. When you are ready to continue, click Resume Seven Zip. This suspends and resumes the process; it does not cancel the extraction."
    },
    [pscustomobject]@{
        Title = "Example Workflows"
        Bullets = @(
            "Backup drive: alert at 100 GB free",
            "USB drive: alert at 10 percent free",
            "Large archive: pause 7-Zip while freeing space"
        )
        Voice = "Here are three examples. For a backup drive, use size mode and set the threshold to one hundred gigabytes. For a USB drive, use percent mode and set it to ten percent. For a large archive extraction, monitor the target drive and pause Seven Zip if free space is getting tight. If Seven Zip was started as administrator, run this app as administrator too."
    },
    [pscustomobject]@{
        Title = "Where to Find the Files"
        Bullets = @(
            "Source: disk_space_monitor_v1_3.py",
            "EXE: dist/DiskSpaceMonitor_v1_3.exe",
            "README includes setup and troubleshooting"
        )
        Voice = "The current source file is disk space monitor version one three dot py. The standalone executable is in the dist folder as Disk Space Monitor version one three dot exe. The README explains requirements, build steps, usage, troubleshooting, and the version history. That is the full tour of Disk Space Monitor version 1.3."
    }
)

function Wrap-Text {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [System.Drawing.Font]$Font,
        [int]$MaxWidth
    )

    $words = $Text -split "\s+"
    $lines = New-Object System.Collections.Generic.List[string]
    $line = ""

    foreach ($word in $words) {
        $candidate = if ($line.Length -eq 0) { $word } else { "$line $word" }
        $size = $Graphics.MeasureString($candidate, $Font)
        if ($size.Width -le $MaxWidth) {
            $line = $candidate
        }
        else {
            if ($line.Length -gt 0) {
                $lines.Add($line)
            }
            $line = $word
        }
    }

    if ($line.Length -gt 0) {
        $lines.Add($line)
    }

    return $lines
}

function Draw-WrappedText {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [System.Drawing.Font]$Font,
        [System.Drawing.Brush]$Brush,
        [int]$X,
        [int]$Y,
        [int]$MaxWidth,
        [int]$LineHeight
    )

    $currentY = $Y
    foreach ($line in (Wrap-Text -Graphics $Graphics -Text $Text -Font $Font -MaxWidth $MaxWidth)) {
        $Graphics.DrawString($line, $Font, $Brush, $X, $currentY)
        $currentY += $LineHeight
    }
    return $currentY
}

function Render-Slide {
    param(
        [pscustomobject]$Slide,
        [int]$Index,
        [string]$Path
    )

    $width = 1280
    $height = 720
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    $background = [System.Drawing.Color]::FromArgb(246, 248, 251)
    $accent = [System.Drawing.Color]::FromArgb(36, 99, 235)
    $ink = [System.Drawing.Color]::FromArgb(24, 35, 51)
    $muted = [System.Drawing.Color]::FromArgb(90, 101, 119)
    $panel = [System.Drawing.Color]::FromArgb(255, 255, 255)
    $lineColor = [System.Drawing.Color]::FromArgb(218, 226, 237)

    $graphics.Clear($background)

    $panelBrush = New-Object System.Drawing.SolidBrush $panel
    $accentBrush = New-Object System.Drawing.SolidBrush $accent
    $inkBrush = New-Object System.Drawing.SolidBrush $ink
    $mutedBrush = New-Object System.Drawing.SolidBrush $muted
    $linePen = New-Object System.Drawing.Pen $lineColor, 2

    $titleFont = New-Object System.Drawing.Font "Segoe UI", 42, ([System.Drawing.FontStyle]::Bold)
    $bulletFont = New-Object System.Drawing.Font "Segoe UI", 27, ([System.Drawing.FontStyle]::Regular)
    $smallFont = New-Object System.Drawing.Font "Segoe UI", 18, ([System.Drawing.FontStyle]::Regular)
    $monoFont = New-Object System.Drawing.Font "Consolas", 20, ([System.Drawing.FontStyle]::Regular)

    $graphics.FillRectangle($accentBrush, 0, 0, 18, $height)
    $graphics.FillRectangle($panelBrush, 70, 72, 1140, 548)
    $graphics.DrawRectangle($linePen, 70, 72, 1140, 548)

    $graphics.DrawString($Slide.Title, $titleFont, $inkBrush, 110, 108)
    $graphics.DrawLine($linePen, 110, 185, 1170, 185)

    $y = 230
    foreach ($bullet in $Slide.Bullets) {
        $graphics.FillEllipse($accentBrush, 116, ($y + 12), 13, 13)
        $y = Draw-WrappedText -Graphics $graphics -Text $bullet -Font $bulletFont -Brush $inkBrush -X 150 -Y $y -MaxWidth 940 -LineHeight 40
        $y += 24
    }

    if ($Index -eq 4) {
        $example = "Threshold reached: YES    Popup monitoring: ON"
        $graphics.FillRectangle((New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(235, 244, 255))), 150, 500, 780, 54)
        $graphics.DrawString($example, $monoFont, $accentBrush, 172, 512)
    }

    $footer = "Disk Space Monitor v1.3 feature walkthrough"
    $slideNumber = "Slide $Index of $($slides.Count)"
    $graphics.DrawString($footer, $smallFont, $mutedBrush, 110, 650)
    $graphics.DrawString($slideNumber, $smallFont, $mutedBrush, 1035, 650)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphics.Dispose()
    $bitmap.Dispose()
    $panelBrush.Dispose()
    $accentBrush.Dispose()
    $inkBrush.Dispose()
    $mutedBrush.Dispose()
    $linePen.Dispose()
    $titleFont.Dispose()
    $bulletFont.Dispose()
    $smallFont.Dispose()
    $monoFont.Dispose()
}

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synth.SelectVoice($VoiceName)
}
catch {
    Write-Host "Voice '$VoiceName' was not available. Using the default Windows voice."
}
$synth.Rate = $Rate

$transcriptLines = New-Object System.Collections.Generic.List[string]
$concatLines = New-Object System.Collections.Generic.List[string]

for ($i = 0; $i -lt $slides.Count; $i++) {
    $slideNumber = $i + 1
    $slide = $slides[$i]
    $slidePath = Join-Path $SlideDir ("slide_{0:00}.png" -f $slideNumber)
    $audioPath = Join-Path $AudioDir ("voice_{0:00}.wav" -f $slideNumber)
    $segmentPath = Join-Path $SegmentDir ("segment_{0:00}.mp4" -f $slideNumber)

    Render-Slide -Slide $slide -Index $slideNumber -Path $slidePath

    $synth.SetOutputToWaveFile($audioPath)
    $synth.Speak($slide.Voice)
    $synth.SetOutputToNull()

    & ffmpeg -y -loop 1 -i $slidePath -i $audioPath -c:v libx264 -tune stillimage -c:a aac -b:a 160k -pix_fmt yuv420p -shortest -vf "fps=30,format=yuv420p" $segmentPath | Out-Null

    $safeSegment = $segmentPath.Replace("\", "/")
    $concatLines.Add("file '$safeSegment'")
    $transcriptLines.Add("Slide $slideNumber - $($slide.Title)")
    $transcriptLines.Add($slide.Voice)
    $transcriptLines.Add("")
}

$concatLines | Set-Content -Path $ConcatList -Encoding ASCII
$transcriptLines | Set-Content -Path $TranscriptPath -Encoding UTF8

& ffmpeg -y -f concat -safe 0 -i $ConcatList -c copy $OutputVideo | Out-Null

Write-Host "Created video: $OutputVideo"
Write-Host "Created transcript: $TranscriptPath"
