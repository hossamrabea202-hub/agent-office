# Vesna's Trade (#361): renders the frame, the atlas and the check mock-ups with headless Edge.
#   powershell -File render.ps1            -> out/T_VT_Frame.png (1920x1080, portrait hole), out/T_VT_Atlas.png (2048x2048),
#                                             out/mock.png, out/overlay.png (1672x941, vs the owner's target)
param([string]$Only = '')
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $here 'out'; New-Item -ItemType Directory -Force $out | Out-Null
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
Add-Type -AssemblyName System.Drawing
function Shot($page, $query, $w, $h, $file, $scale, [switch]$clear) {
  $u = ([uri](Join-Path $here $page)).AbsoluteUri + $query
  $a = @('--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files', '--virtual-time-budget=5000',
         "--window-size=$w,$h", "--force-device-scale-factor=$scale", "--screenshot=$file")
  if ($clear) { $a += '--default-background-color=00000000' }
  & $edge @a $u 2>$null | Out-Null
}
function Fit($file, $w, $h) {   # crop/pad to the exact texture size (Edge rounds the scaled window)
  $src = [System.Drawing.Image]::FromFile($file)
  $bmp = New-Object System.Drawing.Bitmap $w, $h, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::Transparent)
  $g.DrawImage($src, 0, 0, $src.Width, $src.Height); $g.Dispose(); $src.Dispose()
  $bmp.Save($file + '.tmp.png', [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
  Move-Item -Force ($file + '.tmp.png') $file
}
$S = 1920.0 / 1672
& 'U:\5.2\python\bin\python.exe' (Join-Path $here 'layout.py')
if (!$Only -or $Only -eq 'frame') { Shot 'chrome.html' '?m=chrome' 1672 941 "$out\T_VT_Frame.png" $S -clear; Fit "$out\T_VT_Frame.png" 1920 1080 }
if (!$Only -or $Only -eq 'atlas') { Shot 'atlas.html' '' 1783 1783 "$out\T_VT_Atlas.png" $S -clear; Fit "$out\T_VT_Atlas.png" 2048 2048
                                    Shot 'atlas.html' '?grid=1' 1783 1783 "$out\atlas_grid.png" 1 }
if (!$Only -or $Only -eq 'mock')  { Shot 'chrome.html' '?m=mock' 1672 941 "$out\mock.png" 1; Shot 'chrome.html' '?m=overlay' 1672 941 "$out\overlay.png" 1 }
Get-ChildItem $out -Filter *.png | ForEach-Object { $i = [System.Drawing.Image]::FromFile($_.FullName); '{0} {1}x{2}' -f $_.Name, $i.Width, $i.Height; $i.Dispose() }

