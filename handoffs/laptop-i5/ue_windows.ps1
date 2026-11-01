# i5 helper: list the Unreal editor's visible windows; -CloseExtra closes every one except the main editor window
# (floating Message Log / Content Browser / asset editors steal keyboard focus from the console), then focuses the main one.
#   -Focus "<window title>" focuses that window instead (asset editors open as their own OS windows).
param([switch]$CloseExtra, [string]$Focus)
Add-Type @'
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public class UEW { public delegate bool EP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EP f, IntPtr l);
 [DllImport("user32.dll")] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
 public static List<KeyValuePair<IntPtr, string>> List(uint pid) { var r = new List<KeyValuePair<IntPtr, string>>(); EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
   if (p == pid && IsWindowVisible(h)) { var sb = new StringBuilder(256); GetWindowText(h, sb, 256); r.Add(new KeyValuePair<IntPtr, string>(h, sb.ToString())); } return true; }, IntPtr.Zero); return r; } }
'@
$ue = Get-Process UnrealEditor | Select-Object -First 1
$main = $null
foreach ($w in [UEW]::List([uint32]$ue.Id)) {
  if ($Focus -and $w.Value -eq $Focus) { $main = $w.Key; "focus $($w.Key) '$($w.Value)'" }
  elseif ($w.Value -like 'CastleDefender - Unreal Editor') { if (-not $Focus) { $main = $w.Key }; "main  $($w.Key) '$($w.Value)'" }
  elseif ($CloseExtra -and $w.Value) { [UEW]::PostMessage($w.Key, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null; "close $($w.Key) '$($w.Value)'" }
  else { "other $($w.Key) '$($w.Value)'" }
}
if ($main) { Start-Sleep -Milliseconds 500; [UEW]::ShowWindow($main, 3) | Out-Null; [UEW]::SetForegroundWindow($main) | Out-Null }
