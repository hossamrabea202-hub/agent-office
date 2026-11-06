# #543 info card (TGA PC): T_InfoCard_Ulfberht.png, 2048 x 1280, from the lookdev sword picture + the facts below.
# Run: powershell -File make_card543.ps1   (needs work\out\renders\ld_swordcard.png). Facts are kept to what the
# scholarship agrees on; the debated points say so.
Add-Type -AssemblyName System.Drawing
$here = $PSScriptRoot; $W = 2048; $H = 1280
$out = Join-Path $here 'work\out\tex\T_InfoCard_Ulfberht.png'
$bmp = New-Object System.Drawing.Bitmap $W, $H; $g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'; $g.InterpolationMode = 'HighQualityBicubic'
function C($r, $gg, $b, $a = 255) { [System.Drawing.Color]::FromArgb($a, $r, $gg, $b) }
# background: dark oak-brown plate, a soft vignette, a gold rule border
$rect = New-Object System.Drawing.Rectangle 0, 0, $W, $H
$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, (C 44 34 26), (C 22 17 13), 90.0
$g.FillRectangle($bg, $rect)
$path = New-Object System.Drawing.Drawing2D.GraphicsPath; $path.AddEllipse(-300, -200, $W + 600, $H + 400)
$pg = New-Object System.Drawing.Drawing2D.PathGradientBrush $path; $pg.CenterColor = (C 0 0 0 0); $pg.SurroundColors = @((C 0 0 0 150)); $g.FillRectangle($pg, $rect)
$gold = C 201 164 92; $goldDim = C 150 120 70
$g.DrawRectangle((New-Object System.Drawing.Pen $gold, 6), 28, 28, $W - 56, $H - 56)
$g.DrawRectangle((New-Object System.Drawing.Pen $goldDim, 2), 46, 46, $W - 92, $H - 92)
$fT = New-Object System.Drawing.Font('Georgia', 92, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$fS = New-Object System.Drawing.Font('Georgia', 40, [System.Drawing.FontStyle]::Italic, [System.Drawing.GraphicsUnit]::Pixel)
$fH = New-Object System.Drawing.Font('Georgia', 36, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$fB = New-Object System.Drawing.Font('Georgia', 33, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$fN = New-Object System.Drawing.Font('Georgia', 26, [System.Drawing.FontStyle]::Italic, [System.Drawing.GraphicsUnit]::Pixel)
$ink = New-Object System.Drawing.SolidBrush (C 236 226 205); $soft = New-Object System.Drawing.SolidBrush (C 196 184 160); $gb = New-Object System.Drawing.SolidBrush $gold
$g.DrawString('HISTORIC FIND', $fH, $gb, 110, 92)
$g.DrawString('The Ulfberht Sword', $fT, $ink, 100, 132)
$g.DrawString(("Viking Age, about 800 - 1000 AD  " + [char]0x00B7 + "  Northern Europe"), $fS, $soft, 108, 248)
# the sword picture (hilt left, so +VLFBERH+T reads from the hilt as on the real blades)
$sw = [System.Drawing.Image]::FromFile((Join-Path $here 'work\out\renders\ld_swordcard.png')); $sw.RotateFlip('Rotate180FlipNone')
$g.DrawImage($sw, (New-Object System.Drawing.Rectangle 174, 292, 1700, 312), (New-Object System.Drawing.Rectangle 0, 180, $sw.Width, 440), 'Pixel')
$g.DrawLine((New-Object System.Drawing.Pen $goldDim, 2), 110, 620, $W - 110, 620)
function Para($text, $x, $y, $w, $h, $font, $brush) { $g.DrawString($text, $font, $brush, (New-Object System.Drawing.RectangleF $x, $y, $w, $h)) }
$colW = 880
$g.DrawString('WHAT IT IS', $fH, $gb, 110, 645)
Para 'A double-edged Viking sword with the name +VLFBERH+T inlaid in iron near the hilt. About 170 are known, most found in Scandinavia, many in rivers and graves.' 110 693 $colW 200 $fB $ink
$g.DrawString('WHY IT MATTERS', $fH, $gb, 110, 895)
Para 'The best of them are crucible steel: purer and harder than almost any steel smiths in Europe could make then. Where that steel came from is still debated; one idea is trade along the Volga with Central Asia.' 110 943 $colW 250 $fB $ink
$x2 = 1080
$g.DrawString('DID YOU KNOW?', $fH, $gb, $x2, 645)
$facts = @(
  'Ulfberht swords were made for over 200 years, so the name was probably a workshop or a brand, not one smith.',
  'Fakes existed: cheaper copies often spell it wrongly, such as +VLFBERHT+.',
  'Length about 1 m, weight about 1.2 kg: light and quick in the hand.'
)
$y = 695
foreach ($f in $facts) { $g.FillEllipse($gb, $x2, $y + 14, 12, 12); Para $f ($x2 + 30) $y 840 160 $fB $ink; $y += 158 }
Para 'Found in the mine. The find is part of the game; the sword type is real history.' 110 1180 1800 60 $fN $soft
$g.Dispose(); $bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose(); $sw.Dispose()
"CARD OK $out"

