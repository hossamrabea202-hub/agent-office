param([string]$Title = "BPC_TentacleStrike", [int]$EditorPid = 4604, [int]$Show = 3)
# Bring the editor window whose title contains $Title (owned by the editor process) to the front.
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class W {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e);
}
"@
$found = $null
$cb = [W+EnumProc]{ param($h, $l)
  $p = 0; [void][W]::GetWindowThreadProcessId($h, [ref]$p)
  if ($p -eq $EditorPid -and [W]::IsWindowVisible($h)) {
    $sb = New-Object Text.StringBuilder 512; [void][W]::GetWindowText($h, $sb, 512); $t = $sb.ToString()
    if ($t -like "*$Title*") { $script:found = $h; return $false }
  }
  return $true }
[void][W]::EnumWindows($cb, [IntPtr]::Zero)
if (-not $found) { "not found: $Title"; exit 1 }
[W]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [W]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)  # Alt tap lets SetForegroundWindow through
[void][W]::ShowWindow($found, $Show); if ($Show -ne 6) { [void][W]::SetForegroundWindow($found) }  # 3 maximize, 6 minimize
"focused $Title"
