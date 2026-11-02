# #411: T_HUD_CastleKey.png (512 px) from the skill-tree key medallion: the tree emblem is replaced by a castle in the
# same cream/bronze palette with a glowing gate (the red-node glow), and the badge letter T becomes K (Keep; C is the Commander key) (i5 core, 2026-11-01).
#   powershell -File make_castle_icon.ps1
Add-Type -AssemblyName System.Drawing
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = [System.Drawing.Bitmap]::FromFile("$here\ref\T_HUD_SkillTreeKey.png")
$bmp = New-Object System.Drawing.Bitmap 512, 512, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'; $g.TextRenderingHint = 'AntiAliasGridFit'
$g.DrawImage($src, 0, 0, 512, 512); $src.Dispose()
$C = { param($r, $gg, $b, $a = 255) [System.Drawing.Color]::FromArgb($a, $r, $gg, $b) }

# 1. clear the tree: dark leather disc (radial), with a little grain
$cx = 236; $cy = 236; $R = 173
$path = New-Object System.Drawing.Drawing2D.GraphicsPath; $path.AddEllipse($cx - $R, $cy - $R, 2 * $R, 2 * $R)
$pgb = New-Object System.Drawing.Drawing2D.PathGradientBrush $path
$pgb.CenterColor = & $C 44 26 15; $pgb.SurroundColors = @(& $C 16 8 3)
$g.FillPath($pgb, $path)
$rnd = New-Object System.Random 411
for ($i = 0; $i -lt 2600; $i++) {
  $a = $rnd.NextDouble() * 6.2832; $d = [Math]::Sqrt($rnd.NextDouble()) * ($R - 4)
  $x = $cx + $d * [Math]::Cos($a); $y = $cy + $d * [Math]::Sin($a); $v = $rnd.Next(0, 2)
  $br = New-Object System.Drawing.SolidBrush ($(if ($v) { & $C 70 44 26 40 } else { & $C 0 0 0 50 }))
  $g.FillRectangle($br, [float]$x, [float]$y, 2, 2); $br.Dispose()
}

# 2. the castle (512-px coordinates)
$cast = New-Object System.Drawing.Drawing2D.GraphicsPath
function block($x0, $x1, $top, $h, $bottom) {      # wall block [x0,x1] from bottom up to top, 5 merlons/gaps of height h
  $L = New-Object 'System.Collections.Generic.List[System.Drawing.PointF]'
  $L.Add((New-Object System.Drawing.PointF ([float]$x0), ([float]$bottom)))
  $w = ($x1 - $x0) / 5.0
  for ($k = 0; $k -lt 5; $k++) {
    $a = $x0 + $k * $w; $y = if ($k % 2 -eq 0) { $top } else { $top + $h }
    $L.Add((New-Object System.Drawing.PointF ([float]$a), ([float]$y))); $L.Add((New-Object System.Drawing.PointF ([float]($a + $w)), ([float]$y)))
  }
  $L.Add((New-Object System.Drawing.PointF ([float]$x1), ([float]$bottom)))
  return ,$L.ToArray()
}
function poly($pts) {
  $L = New-Object 'System.Collections.Generic.List[System.Drawing.PointF]'
  foreach ($q in $pts) { $L.Add((New-Object System.Drawing.PointF ([float]$q[0]), ([float]$q[1]))) }
  return ,$L.ToArray()
}
$base = 332
$cast.AddPolygon((block 150 322 238 12 $base))                                  # curtain wall
foreach ($tx in 124, 300) { $cast.AddPolygon((block $tx ($tx + 52) 168 13 $base)) }   # towers
$cast.AddPolygon((block 198 274 140 12 250))                                    # keep
$cast.FillMode = 'Winding'
$lg = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.Point 0, 136), (New-Object System.Drawing.Point 0, 336), (& $C 236 216 174), (& $C 158 108 46)
$g.FillPath($lg, $cast)
# stone courses (faint)
$pen = New-Object System.Drawing.Pen (& $C 90 58 24 70), 2
foreach ($y in 262, 286, 310) { $g.DrawLine($pen, 152, $y, 320, $y) }
foreach ($y in 196, 224, 252, 280, 308) { $g.DrawLine($pen, 126, $y, 174, $y); $g.DrawLine($pen, 302, $y, 350, $y) }
foreach ($y in 170, 198, 226) { $g.DrawLine($pen, 200, $y, 272, $y) }
$out = New-Object System.Drawing.Pen (& $C 52 30 12), 5; $out.LineJoin = 'Round'
$g.DrawPath($out, $cast)
# gate glow + arch
$glow = New-Object System.Drawing.Drawing2D.GraphicsPath; $glow.AddEllipse(186, 262, 100, 100)
$gb = New-Object System.Drawing.Drawing2D.PathGradientBrush $glow; $gb.CenterColor = & $C 220 70 40 150; $gb.SurroundColors = @(& $C 220 70 40 0)
$g.FillPath($gb, $glow)
$gate = New-Object System.Drawing.Drawing2D.GraphicsPath
$gate.AddArc(214, 276, 44, 44, 180, 180); $gate.AddLine(258, 298, 258, $base); $gate.AddLine(258, $base, 214, $base); $gate.CloseFigure()
$gg = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.Point 0, 276), (New-Object System.Drawing.Point 0, 334), (& $C 255 196 120), (& $C 190 60 30)
$g.FillPath($gg, $gate); $g.DrawPath($out, $gate)
$port = New-Object System.Drawing.Pen (& $C 70 30 10 200), 3
foreach ($x in 225, 236, 247) { $g.DrawLine($port, $x, 282, $x, $base - 2) }
# arrow slits
$slit = New-Object System.Drawing.SolidBrush (& $C 34 18 8)
foreach ($s in @(@(146, 214), @(146, 262), @(322, 214), @(322, 262), @(230, 176), @(230, 212))) {
  $sp = New-Object System.Drawing.Drawing2D.GraphicsPath; $sp.AddArc($s[0], $s[1], 12, 12, 180, 180); $sp.AddLine($s[0] + 12, $s[1] + 6, $s[0] + 12, $s[1] + 26)
  $sp.AddLine($s[0] + 12, $s[1] + 26, $s[0], $s[1] + 26); $sp.CloseFigure(); $g.FillPath($slit, $sp)
}
# banner on the keep
$g.DrawLine((New-Object System.Drawing.Pen (& $C 52 30 12), 4), 236, 140, 236, 96)
$flag = poly @(@(238, 98), @(276, 108), @(238, 120)); $g.FillPolygon((New-Object System.Drawing.SolidBrush (& $C 196 52 36)), $flag)
$g.DrawPolygon((New-Object System.Drawing.Pen (& $C 70 20 10), 2), $flag)
# ground line
$g.DrawLine((New-Object System.Drawing.Pen (& $C 120 82 36), 4), 112, ($base + 2), 360, ($base + 2))

# 3. badge: T -> K
$ib = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.Point 0, 356), (New-Object System.Drawing.Point 0, 468), (& $C 40 40 36), (& $C 14 14 12)
$g.FillRectangle($ib, 374, 360, 112, 104)
$f = New-Object System.Drawing.Font 'Georgia', 72, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$sf = New-Object System.Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.LineAlignment = 'Center'
$rect = New-Object System.Drawing.RectangleF 374, 362, 112, 104
$g.DrawString('K', $f, (New-Object System.Drawing.SolidBrush (& $C 0 0 0 160)), (New-Object System.Drawing.RectangleF 377, 366, 112, 104), $sf)
$tg = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.Point 0, 370), (New-Object System.Drawing.Point 0, 456), (& $C 246 214 140), (& $C 176 118 48)
$g.DrawString('K', $f, $tg, $rect, $sf)

$g.Dispose()
New-Item -ItemType Directory -Force "$here\build" | Out-Null
$bmp.Save("$here\build\T_HUD_CastleKey.png", [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
"saved $here\build\T_HUD_CastleKey.png"

