# Vesna #380 step 3: merge the ArmoryHUD hook into your fresh export.
# Before: open BP_ArmoryHUD EventGraph, Ctrl+A, Ctrl+C, paste into Notepad, save as C:\Users\hossa\Documents\live.t3d
import subprocess, os, unreal
R = r'C:\Users\hossa\Documents\agent-office'
live = r'C:\Users\hossa\Documents\live.t3d'; out = r'C:\Users\hossa\Documents\merged.t3d'
py = r'C:\Program Files\Epic Games\UE_5.3\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
if not os.path.exists(live): unreal.log_error('VESNA: live.t3d not found at ' + live); raise SystemExit
r = subprocess.run([py, os.path.join(R, 'tools', 'applyall', 'applyall.py'), 'merge', '--live', live, '--manifest',
                    os.path.join(R, 'handoffs', 'vesna-trade-361', 'build', 'manifest_trade.json'), '--out', out], capture_output=True, text=True)
unreal.log('VESNA MERGE rc=%d\n%s\n%s' % (r.returncode, r.stdout[-3000:], r.stderr[-2000:]))
unreal.log('VESNA: if it says Validation: OK -> in BP_ArmoryHUD EventGraph: Ctrl+A, BackSpace, then paste the contents of merged.t3d, Compile, Save.')
