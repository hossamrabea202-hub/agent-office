# #424: renders T_VT_Frame_424 (6-slot doll), T_VT_Atlas_424 (bundle rows, tier lines, outline glyphs) and the check
# mock-up with headless Edge, from tools/tga/vesna/{chrome,atlas}.html?L=bd (layout_bd.py).
#   powershell -ExecutionPolicy Bypass -File render_bd.ps1
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$kit = Resolve-Path (Join-Path $here '..\..\..\tools\tga\vesna')
$tex = Join-Path $here '..\textures'; $ren = Join-Path $here '..\renders'
New-Item -ItemType Directory -Force $tex, $ren | Out-Null
$tex = Resolve-Path $tex; $ren = Resolve-Path $ren
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
Add-Type -AssemblyName System.Drawing
function Shot($page, $query, $w, $h, $file, $scale, [switch]$clear) {
  $u = ([uri](Join-Path $kit $page)).AbsoluteUri + $query
  $a = @('--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files', '--virtual-time-budget=8000',
         "--window-size=$w,$h", "--force-device-scale-factor=$scale", "--screenshot=$file")
  if ($clear) { $a += '--default-background-color=00000000' }
  & $edge @a $u 2>$null | Out-Null
}
function Fit($file, $w, $h) {
  $src = [System.Drawing.Image]::FromFile($file)
  $bmp = New-Object System.Drawing.Bitmap $w, $h, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::Transparent)
  $g.DrawImage($src, 0, 0, $src.Width, $src.Height); $g.Dispose(); $src.Dispose()
  $bmp.Save($file + '.tmp.png', [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
  Move-Item -Force ($file + '.tmp.png') $file
}
$S = 1920.0 / 1672
python (Join-Path $kit 'layout_bd.py')
Shot 'chrome.html' '?m=chrome&L=bd' 1672 941 "$tex\T_VT_Frame_424.png" $S -clear; Fit "$tex\T_VT_Frame_424.png" 1920 1080
Shot 'atlas.html' '?L=bd' 1783 1783 "$tex\T_VT_Atlas_424.png" $S -clear; Fit "$tex\T_VT_Atlas_424.png" 2048 2048
Shot 'atlas.html' '?L=bd&grid=1' 1783 1783 "$ren\atlas_424_grid.png" 1
Shot 'chrome.html' '?m=mock&L=bd' 1672 941 "$ren\mock_424.png" 1
Get-ChildItem $tex, $ren -Filter *.png | ForEach-Object { $i = [System.Drawing.Image]::FromFile($_.FullName); '{0} {1}x{2}' -f $_.Name, $i.Width, $i.Height; $i.Dispose() }
