# Laptop i5: what was done on this machine, and how to pick it up

Machine: the owner's **laptop with the 12th Gen Intel i5-1235U + NVIDIA MX570** (Windows user `hossam.rabea`,
repo at `C:\Users\hossam.rabea\agent-office`). Seat used here: **`checkking (Claude)`** (3D / VFX / tech art,
desks #7 and #12). Written 2026-10-31 by checkking before its session ran out of context.
**Any agent on this laptop can continue from here.** Read `AGENTS.md` first.

## Tools on this laptop

| What | Where |
|---|---|
| Blender 4.5 (Cycles, OptiX on the MX570) | `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe` |
| Python 3.11 (no system Python; use Blender's) | `C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe -I` |
| Short work folder (Blender can't open paths over 260 characters) | `C:\Users\hossam.rabea\ckw\` |
| T3D readers (inspect any Blueprint export) | `ckw\t3d.py FILE NODE...` (node + links), `ckw\walk.py FILE START N` (exec chain), `ckw\find.py FILE "value"`, `ckw\flatten.py BP.T3D EventGraph out.txt` (whole-BP export to a flat graph for applyall dry-runs) |
| Weapon batch / sheet | `ckw\batch_weapons.sh` (`WEAPONS="a b c" sh ...`), `ckw\weapon_sheet.py` |
| Graph builder | `tools/laptop2/bpgen/bpkit.py` (on the Master's `tools/master/t81/kit.py`). Pre-check: `tools/applyall/fix_impure.py`, then `applyall.py check` / `merge --dry-run` |

Git note: background bakes write into `assets/`, so pull with `git stash push -u; git pull --rebase; git push; git stash pop`.

## Everything checkking did here (2026-10-30 / 31)

| Hand-off | What | Folder | Status |
|---|---|---|---|
| #221 / #222 | Obsidian set v2: tiered bonus, pieces on the hero, Vesna Obsidian Armoury panel, save | `handoffs/obsidian-set-v2` | **in the game** (Master, night of 10-30) |
| #231 | Motion graphics: book and satchel 3D reveals, auto-open, how-to cards (#86 inside), infection-look add-on #141 | `handoffs/motion-graphics-66`, `assets/checkking/RevealMG` | **in the game**, except the skill-tree T auto-open (needs 4 nodes, see the Master's notes) and #141 (after #148) |
| #232 | #213 PRIORITY: skill-tree UNLOCK hit the invisible Quit | `handoffs/skilltree-quit-213` | queued, pre-checked |
| #234 | #217 floating bolts | `handoffs/bolts-217` | queued |
| #235 / #236 | #214 crossbow fire rate, #216 aim backwards | `handoffs/xbow-firerate-214` | queued (#214 pre-checked) |
| #237 | #219 courtyard rock script | `handoffs/courtyard-rock-219` | queued |
| #238 | #220 soldier unstick redo | `handoffs/soldier-unstick-220` | queued, pre-checked |
| #239 | #230 deploy cannon (BP_CannonOrder + BP_CannonConvoy) | `handoffs/deploy-cannon-230` | queued, pre-checked |
| #233 | Weapon kit: **25 weapons**, 2K PBR, one import script | `assets/checkking/Weapons` (+ `source/build_weapon.py`) | queued for import |
| #254 / #255 | Weapon wiring: WEAPONSMITH panel at Vesna, buy / equip / hold in hand_r, save, damage x Damage/40, attack speed, hide the knight sword | `handoffs/weapon-kit-wiring` | queued, pre-checked |
| #260 | Texture budget script (Maximum Texture Size by folder, dry-run first) | `handoffs/texture-budget` | queued |
| #264 | Infection downsides: walk x0.75, 25 % missed hits (after #255) | `handoffs/infection-downsides-263` | queued, **after #266** |
| #265 | Castle stones merge: thousands of stone actors -> one Nanite mesh per wall section | `handoffs/castle-stones-merge` | queued (back up the map first) |
| #58 | Cannon break stages: automatic Blender script | `handoffs/cannon-break-58` | **waits on export #241** (SM_FieldCannon_HD) |
| #256 / #258 | Torn cape masks (done) + cape as a wearable item with repair at Vesna (card) | `assets/checkking/TornCape` | **waits on the cape material export** |

Cards filed for the owner: #223 farming (now TGA's, v1 handed off as #259), #224-#227 systems, #261 trim sheets (**Master only**,
licensed textures), #262 texture plan (TGA), #266 **PRIORITY infection cure** (Master pastes #148 first).

## What is open / next

1. **#58:** when `handoffs/exports/checkking/cannon/SM_FieldCannon_HD.fbx` lands, run
   `blender -b --factory-startup -P handoffs/cannon-break-58/break_cannon.py -- <fbx> <out> SM_FieldCannon_HD`,
   check `renders/break_stages.png`, then write the import + StageMeshes script and hand it off.
2. **Torn cape (#256 / #258):** when the cape material export lands, build the material instance (tear = opacity mask
   `CapeWear > R`, dirt G, blood B, fray A), the CapeWear driver (hero damage up; weapon buy / upgrade or the paid Vesna
   repair resets it), the cape item slot (+10 % DEF, +10 % HP) and the stitch-back motion graphic.
3. **#213 part 2 / #218:** need a screenshot (UNLOCK boxes over the aura names / army slots 4/6).
4. **The 6 missing Obsidian pieces** (helmet, cape, thighs, waist, forearms, upper arms): see
   `handoffs/checkking-session/HANDOFF.md` for the pipeline. Mesh names must match `handoffs/obsidian-set-v2/pieces.csv`.

## Owner rules learned this session (also in AGENTS.md)

- The Master only pastes finished, pre-checked work. Small one-minute fixes are fine for the Master.
- Characters: AI-made Blender humans aren't AAA. Use MetaHuman (the Master in Unreal) for farmers and villagers.
- Texture budget: hero armour, enemies and rocks 2K; weapons, props and gear 1K; tiny props 512.
- The owner likes the tanky last 30 % HP (infection +50 % DEF) but the **cure must always exist** (#266).
