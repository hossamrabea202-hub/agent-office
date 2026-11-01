# Chat Bubble (i5 core, 2026-11-01, owner Alien): a small always-on-top round icon for the studio chat.
#  - drag it anywhere (it remembers the spot), right-click for Open / Mark read / Quit
#  - a red badge counts new chat lines (everyone's, or only others' with -Me "Alien")
#  - double-click opens the chat page and clears the count
# Run:  powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File ChatBubble.ps1 [-Server http://100.87.149.123:8765] [-Me Alien]
param([string]$Server = 'http://100.87.149.123:8765', [string]$Me = '')
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$state = Join-Path $env:APPDATA 'ChatBubble.json'
$cfg = @{ last = 0; x = 40; y = 200 }
try { if (Test-Path $state) { $j = Get-Content $state -Raw | ConvertFrom-Json; $cfg.last = [int]$j.last; $cfg.x = [int]$j.x; $cfg.y = [int]$j.y } } catch {}
function Save { try { $cfg | ConvertTo-Json | Set-Content $state -Encoding utf8 } catch {} }

$f = New-Object Windows.Forms.Form
$f.FormBorderStyle = 'None'; $f.TopMost = $true; $f.ShowInTaskbar = $false
$f.StartPosition = 'Manual'; $f.Size = New-Object Drawing.Size(64, 64); $f.Location = New-Object Drawing.Point($cfg.x, $cfg.y)
$f.BackColor = [Drawing.Color]::Magenta; $f.TransparencyKey = [Drawing.Color]::Magenta
$script:count = 0; $script:online = $true
$f.Add_Paint({
    $g = $_.Graphics; $g.SmoothingMode = 'AntiAlias'
    $g.FillEllipse((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(17, 27, 41))), 4, 4, 56, 56)
    $ring = if ($script:online) { [Drawing.Color]::FromArgb(200, 165, 90) } else { [Drawing.Color]::Gray }
    $g.DrawEllipse((New-Object Drawing.Pen($ring, 3)), 4, 4, 56, 56)
    $g.FillRectangle((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(213, 223, 235))), 18, 22, 28, 18)   # speech bubble
    $g.FillPolygon((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(213, 223, 235))), [Drawing.Point[]]@((New-Object Drawing.Point(22, 40)), (New-Object Drawing.Point(30, 40)), (New-Object Drawing.Point(22, 47))))
    if ($script:count -gt 0) {
        $g.FillEllipse([Drawing.Brushes]::Firebrick, 36, 2, 26, 26)
        $t = if ($script:count -gt 99) { '99+' } else { "$script:count" }
        $sf = New-Object Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.LineAlignment = 'Center'
        $g.DrawString($t, (New-Object Drawing.Font('Segoe UI', 8, [Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF(36, 2, 26, 26)), $sf)
    }
})
$path = New-Object Drawing.Drawing2D.GraphicsPath; $path.AddEllipse(2, 0, 62, 62); $f.Region = New-Object Drawing.Region($path)

# drag
$script:drag = $false; $script:off = $null
$f.Add_MouseDown({ if ($_.Button -eq 'Left') { $script:drag = $true; $script:off = $_.Location } })
$f.Add_MouseMove({ if ($script:drag) { $p = [Windows.Forms.Cursor]::Position; $f.Location = New-Object Drawing.Point(($p.X - $script:off.X), ($p.Y - $script:off.Y)) } })
$f.Add_MouseUp({ $script:drag = $false; $cfg.x = $f.Location.X; $cfg.y = $f.Location.Y; Save })

function MarkRead { $script:count = 0; Save; $f.Invalidate() }
function OpenChat { Start-Process $Server; MarkRead }
$f.Add_DoubleClick({ OpenChat })
$menu = New-Object Windows.Forms.ContextMenuStrip
[void]$menu.Items.Add('Open chat', $null, { OpenChat })
[void]$menu.Items.Add('Mark read', $null, { MarkRead })
[void]$menu.Items.Add('Quit', $null, { Save; $f.Close() })
$f.ContextMenuStrip = $menu
$tip = New-Object Windows.Forms.ToolTip; $tip.SetToolTip($f, 'Studio chat - double-click to open')

# poll every 5 s: count new lines (id|time|text), skip my own if -Me is set
$timer = New-Object Windows.Forms.Timer; $timer.Interval = 5000
$timer.Add_Tick({
    try {
        $raw = (New-Object Net.WebClient).DownloadString("$Server/read?after=$($cfg.last)")
        $script:online = $true
        foreach ($line in ($raw -split "`n")) {
            if ($line -match '^(\d+)\|[^|]*\|(.*)$') {
                $id = [int]$matches[1]; if ($id -gt $cfg.last) { $cfg.last = $id }
                if (-not $Me -or $matches[2] -notmatch "^From: $([regex]::Escape($Me))\b") { $script:count++ }
            }
        }
        Save
    } catch { $script:online = $false }
    $f.Invalidate()
})
# first run: start counting from now, not from the whole history
if ($cfg.last -eq 0) {
    try { $raw = (New-Object Net.WebClient).DownloadString("$Server/read?after=0"); $ids = [regex]::Matches($raw, '(?m)^(\d+)\|') | % { [int]$_.Groups[1].Value }; if ($ids) { $cfg.last = ($ids | Measure-Object -Maximum).Maximum } } catch {}
}
$timer.Start()
[Windows.Forms.Application]::Run($f)
