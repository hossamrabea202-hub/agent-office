# Master handover → Vice Master (2026-10-27 night)

From: **hossam gmail (Claude)**, Master Agent (desk #0). I'm out of credits until my recharge.
To: **the Vice Master** — you drive the Unreal editor in my place until I'm back.
When I return, I read **`VICE_REPORT.md`** (same folder) and take over from it. Keep it current as you go.

The owner (hossam) is a beginner with Blueprints. He wants us to drive the editor ourselves. **Keep replies to him very short.** Long answers annoy him.

---

## 1. Your job (same rules as the Master)

- **Only you touch the editor.** Every other seat hands work over (AGENTS.md rule 1). You paste, compile, save, Play-test, close.
- Start each session: `git pull`, then `node tools/office.js inbox --seat "<your seat>"`. Tick your desk after every micro task (`tools/tick.js`).
- **Paste ready hand-offs at once.** Fix small errors yourself. Ack in the cafeteria (issue #25): "Pasting #N" → result.
- **Before any paste, export the live graph.** The queue can be stale.
- **Test it yourself in Play/Simulate.** Never ask the owner to check.
- **Back up every .uasset you replace** into `Tools/PasteRegen_1027/backup_1027/` (or a new dated folder).

## 2. Where things are

| What | Where |
|---|---|
| Project (UE 5.3, Blueprint-only) | `C:\Unreal Backups\Castle Defender` |
| Map | `/Game/ThirdPerson/Maps/ThirdPersonMap` |
| Editor | one `UnrealEditor.exe` on that project (PID changes on restart: `tasklist`) |
| My tools (latest) | `C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027\` |
| Graph exports | `...\PasteRegen_1027\t3d\` (live_*, chk_*, after_*) |
| Backups of replaced assets | `...\PasteRegen_1027\backup_1027\` |
| Office repo | `C:\Users\hossa\Documents\agent-office` (hand-offs in `handoffs/`, exports for agents in `handoffs/exports/`) |
| Editor log | `C:\Unreal Backups\Castle Defender\Saved\Logs\CastleDefender.log` |
| Packaged build | `C:\Unreal Backups\CastleDefender_Build` |

## 3. How to drive the editor

**Script channel (no clicking):**
```powershell
cd "C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027"
.\ue.ps1 my_script.py 60      # copies the script to the watcher (cmd\go.py); waits for result.txt
```
A watcher inside the editor runs `go.py`. Scripts write their own log file next to them (ue.ps1 deletes `<script>.txt` first). Ping: `.\ue.ps1 ping.py`.
If the editor restarted and the watcher is gone, it must be re-armed from the editor's Python console (see `pie_rearm.py`; the watcher folder lives in an old session scratchpad, path inside `ue.ps1`).

**Useful scripts in PasteRegen_1027:**
- `open_bp.py` (+ `open_target.txt` = asset path): opens a BP editor
- `exp_one.py` / `exp_chk.py` / `exp_rev.py`: T3D export
- `pie_start.py` (Simulate) · `pie_end.py` · `pie_slomo.py` (+ `pie_slomo_val.txt`)
- `pie_smoke.py` (+ `pie_smoke_mode.txt` = mark/setup/probe/zombie): counts actors + **runtime errors per Blueprint since the mark**
- `dirty.py` / `save_dirty.py`: unsaved packages / save all
- `focus.ps1 -Title <window title part> -EditorPid <pid> -Show 3|5|6`: bring a window front (3 max, 6 minimize)
- `nodediff.py`, `defdiff.py`, `checklive.py`, `pastecheck.py`: check a paste against the live export
- `kit2.py` + `t3dlib.py`: generator kit (load_graph, clone, link, vget/vset, branch, mcall)

**Graph paste (full-graph replace) — the safe recipe:**
1. Export the live BP → generate the new graph from the **live** export (drop stale nodes: only names in the graph's `Nodes(n)=` list are real).
2. Back up the .uasset. Open the BP (`open_bp.py`), put the T3D on the clipboard (`Set-Clipboard`).
3. Computer use: click empty graph → Ctrl+A → **BackSpace** (Delete key doesn't register) → wait → click → Ctrl+V → Compile → Ctrl+S.
4. Re-export and diff: every pasted node name must be in the live `Nodes()` list, no orphan pins, defaults unchanged (`defdiff.py`).
5. Play/Simulate test + `pie_smoke.py` error count.

**Member variables:** clipboard `BPVar(VarName=...,VarGuid=...,VarType=(...),PropertyFlags=5,DefaultValue="...")` → click the My Blueprint **VARIABLES** header → Ctrl+V. One variable per paste.

## 4. Gotchas that cost me hours (read these!)

1. **Calls to a BP's OWN custom events written with `MemberParent=<own class>` are SILENTLY DROPPED on paste.** Compile still says OK. Write them as `FunctionReference=(MemberName="X",bSelfContext=True)`. On paste a "Fix Self Context" dialog appears → **Confirm** (Do Nothing) → compile shows "<Unnamed> pin" error → **File > Refresh All Nodes** → compile OK. (This broke BP_JellyTrailManager; fixed 10-27.)
2. **Zero defaults:** a pasted pin default of `0` becomes the function's C++ default (Subtract/Add/Multiply/Divide B → 1.0, MakeColor A → 1.0). Never rely on a literal 0 there; run `defdiff.py`.
3. **Impure getters:** some nodes (e.g. KismetMaterialLibrary `GetVectorParameterValue` here) are EXEC nodes. Unwired, they're "pruned" and read zeros. Chain them into the exec line. Check the compiler log for "was pruned".
4. Pure nodes evaluate every input: null guards must be Branch(IsValid) on the exec path.
5. `KismetMathLibrary::Ease` is dropped on paste: use Lerp + Clamp.
6. **Main editor window minimized → floating BP editor windows render blank.** Restore it (ShowWindow 9), re-open the asset with `open_bp.py`.
7. Computer-use clicks can land in the **level viewport** if a different window is in front → actors get selected/moved. Always screenshot first, use `focus.ps1`, and **switch away from Landscape mode** before clicking the viewport.
8. Python can't spawn actors in PIE. Park actors in the editor level first (collision off), move them in PIE, delete before saving the map (`rv_park.py` / `rv_clean.py`).
9. Template/CDO changes do NOT reach placed level instances. Set placed instances too and save the map.
10. Non-instance-editable BP vars can't be set/read from Python on instances (e.g. vitals `Health`, trail `QLoc`).
11. Saves fail silently during PIE. End PIE first.
12. Game starts paused at the menu: `GameplayStatics.set_game_paused(world, False)` or click Begin the Siege. Real Play needs the toolbar Play button (no Python API in 5.3); Simulate = `pie_start.py` (no player → BP_Crossbow/StairPace "Accessed None" spam is normal there).
13. `unreal.Rotator(a,b,c)` = ROLL, PITCH, YAW. Kismet libraries drop the prefix in Python (`unreal.MaterialLibrary`, `unreal.MathLibrary`).
14. Never take high-res screenshots from the watcher (crash). Never PNG-export HDR textures (crash). Never build meshes in-editor with StaticMeshDescription (crash) — write OBJ and import.
15. PowerShell SendKeys don't reach UE. Use computer-use (`mcp__computer-use__*`, editor exe `C:\Program Files\Epic Games\UE_5.3\Engine\Binaries\Win64\UnrealEditor.exe`, display **S27E390**).

## 5. Game systems (short map)

- **HUD chain** (game HUD class = BP_CommanderHUD, child of BP_HeroHUD): ZombieHUD ← Minimap ← SkillTree ← Barracks ← Army ← Controls ← Queue ← Hero ← Commander. **Gold** lives on BP_ZombieHUD (start 500).
- **Tentacles:** BP_TentacleVitals (Health 100k, regen 1000/s) + jelly shell MID (ShieldMax/ShieldLost) + `BPC_TentacleStrike` (revenge strike, below) + ABP_TentacleStrikePP (bone curl). Cannon side: `BPC_CannonBreak` (HP 1200, removes tag `Cannon` when wrecked). 8 placed cannons, all tagged `Cannon`.
- **Revenge strike (10-27):** a tentacle strikes ONE cannon only when HP ≤ 10% (re-arms above 50%) or its jelly shield hits 0% (once). Target = cannon whose ball hit it last (OnRevengeHit bound to hitboxes), else nearest within 19000. One striker at a time. Timings on CDO + all 10 placed instances. Only tentacles 5, 05, Fog1–3 have a cannon in range.
- **Jelly:** cannon hits on shields throw BP_JellyBlob → blobs are **mines** (armed until the hero steps within 110 cm → melt → column → hatch jelly zombie ZType 5). Splat on landing (160) and trigger (220); armed blob in fire pops (no hatch).
- **Fire slime (#32):** BP_JellyTrailManager (ISM ring buffer 600, spatial hash). Jelly zombies lay trail; cannonball blast calls Ignite; fire spreads, burns zombies ×1 (jelly ×2), soldiers ×1, hero ×0.25 (0 with Selfburn).
- **Auras (keys 4/5/6):** BP_HeroAuras + MPC_HeroAbilities (`AuraT_X = OnUntil, CdUntil, Dur, Cd`). **No stacking** (10-27): one active aura locks the other two until it ends. Defense/Heal rings pop in/out.
- **Army:** recruits via barracks (Commander 300 gold, orange cape). E = order wheel (7 orders; Commander has his own wheel). Soldiers level up (BP_SoldierLevelWatch, level-up FX).
- **Zombie charge:** BP_ZombieCharge (in level) makes nearby zombies dash, then cooldown.

## 6. Status at handover

**Done + verified 10-27:** revenge strike (Simulate), trail-manager fix (Simulate), blob splat/pop hooks (Simulate), aura lock + pop-in (Play), Play smoke test 400 s with 0 runtime errors (auras, zombie charge, trails).

**Pasted but NOT seen in Play yet** — do a hands-on test when you can:
- Commander wheel / formation / army counters (recruit needs 300 gold)
- Crossbow aim fix (#26) and faster bolts (#4)
- Soldier level-up FX (#33), slash grows with level (#27/#34)
- Mine trigger by the hero + 220 splat; revenge wind-up look (growl, rear-back)

**Open for the Master seat:**
- Hand-offs #27 #30 #33 #34 #36 are pasted; their GitHub issues are still open (my `office.js close` was blocked by permissions — ask the owner or close them).
- checkking waits on **#19 part 2 export**: hero AnimBP as T3D (all graphs incl. AnimGraph) → `handoffs/exports/checkking/aimspine/` (crossbow aim past 60° via spine bend).
- Office bug from checkking: `.github/workflows/board.yml` sets the bot identity only on the commit (needs a token with `workflow` scope).
- Owner's new ideas pinned for tomorrow: issues #41–#49 (zombie towers, gift zombies/item drops, corpse ramps, night watch, bell lure, 250 m spiral tower). #9 round tower → Codex.
- Possibly missing: hero hard-landing montage (AM_Hero_HardLand) not found in the live hero graph (unconfirmed; maybe intentional).
- Clean-ups: M_UI_BK_Icon + WBP_TentacleHealth can be deleted after an editor restart.

## 7. Memory

My full notes are in `C:\Users\hossa\.claude\projects\C--Users-hossa-OneDrive-Documents-Unreal-Projects-ChatGPT2\memory\` (index `MEMORY.md`). Most useful: `unreal-editor-automation.md`, `master-agent-editor-access.md`, `paste-zero-default-gotcha.md`, `tentacle-revenge-strike.md`, `jelly-trail-fix-blob-hooks-1027.md`, `barracks-commander-card-1027.md`.

---
**Before I come back:** write `VICE_REPORT.md` here (template in that file). One line per thing you pasted/changed, what you verified, what's broken, what's waiting.
