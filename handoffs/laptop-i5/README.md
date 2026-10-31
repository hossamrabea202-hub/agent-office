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

## How to work here: the rules (short version; full text in `AGENTS.md`)

**Start of every session**
1. `git pull`, then read `AGENTS.md` and this page.
2. `node tools/office.js inbox --seat "<seat>"` (add `--all` for the last 15 cafeteria lines).
3. `node tools/tick.js --seat "<seat>" --start --tokens <context tokens> --plan Pro --h5 <5h %> --wk <week %> --working "<task>"`.
   Add `--take-over` only if the old session on this seat is really gone. **One session per seat.**
4. Start the watcher in the background: `node tools/watch.js --seat "<seat>" --every 5`.

**Ticking and reporting**
- Tick when you **start**, **finish** (`--done "<task>" --tokens <n>`, required), get **blocked** (`--ask "<what you need>"`),
  and at least **every 25 minutes**. A desk older than 30 minutes shows offline.
- Report in the cafeteria (issue #25) on events only: finished, handed off, blocked. Talk about one card on that card
  (`say --card <n>`).
- Post a screenshot of every finished visible result: `node tools/shot.js --seat "<seat>" --file <img> --caption "<what>" --card <n>`,
  1280–1600 px wide.

**Non-stop rule**
- Work the whiteboard in order (quick, then medium, then large). Unclear? Decide, write `Decision: ...` on the card and
  keep going.
- Only stop for: spending money, deleting owner data, overwriting the owner's save, or a blocker only the owner can clear.
  Then `--ask`, and switch cards.
- New owner ideas go on the whiteboard as a card first.
- Before your tokens run out, leave a hand-off note on the card you're in the middle of, and update this page.

**The Master only pastes** (owner, 2026-10-31)
- Only the Master touches Unreal. Hand back **finished, pre-checked** work:
  - graph pastes plus an applyall manifest (`fix_impure.py`, then `applyall check` / `merge --dry-run` on the latest export);
  - BPVar lines (no `add_member_variable` from Python);
  - editor scripts with a dry-run mode;
  - an import script, exact steps and a test list.
- Build on a **fresh export**. Missing data? `node tools/office.js request --kind export ...` and keep working.
- Exceptions: one-minute fixes (a wrong default, one missing wire) the Master may do on the spot. Cards marked
  **MASTER ONLY** (licensed textures, MetaHuman) are the Master's.
- In 5.3, `GetActorOfClass`, `GetAllActorsOfClass`, casts and save-game nodes are impure: wire them into the exec chain.
  Calls to a Blueprint's own events use `bSelfContext=True`.

**Quality: AAA and real life, not a game**
- Before any visual work, read `handoffs/knowledge/README.md` and `INDUSTRY_SECRETS.md` (the 10 rules) and apply them. Say
  which rules you applied in the hand-off.
- **Calibrated PBR:**
  - non-metal albedo 30–240 sRGB;
  - bare metal at least 180 sRGB, metallic 0 or 1;
  - Specular 0.5;
  - no lighting baked into the colour.
  
  Run `tools/laptop2/pbr_check.py` before every texture hand-off.
- **Roughness never flat. Wear has a cause, in this order:** edges, cavities, gravity, sun, water. No global grunge.
- **Judge in lookdev** with locked exposure (a 0.18 grey ball): warm key light, cool rim, weak fill.
- **Texture budget** (third-person, by camera distance): hero armour, enemies and rocks 2K; weapons, props and gear 1K;
  tiny props 512.
- **Hard surfaces** (weapons, armour, props, buildings) are made here in Blender, procedurally, at AAA quality.
  **Humans and characters**: MetaHuman (Master) or licensed Fab bases. AI-scripted Blender humans aren't AAA.
- **Never commit licensed assets** (Megascans, Fab, the knight FBX) to the repo. They stay on the owner's PC.
- **Don't break the decal system:** no DBuffer / decal material edits without the owner's OK. Prefer new material
  instances over editing live materials.
- **Keep the look:** changing an existing asset needs a before/after screenshot, and the owner approves it first.

**Owner taste (learned)**
- Short replies, plain words, no jargon.
- Wants visible results and agents that keep working without asking.
- Gameplay: hard but fair (tanky last 30 % HP), but never take away hope (the infection cure must always exist).

---

## adjustedfilm (Claude) on this laptop: 2026-10-31 session

Seat **`adjustedfilm (Claude)`**. The owner confirmed the i5 laptop is adjustedfilm's. Everything below is handed off,
pre-checked (`fix_impure.py` clean, `applyall check` Validation OK, and dry-run merges where the work touches an existing
Blueprint), and waits for the Master's paste.

| Card | Hand-off | What | Folder |
|---|---|---|---|
| #268 | #269 | AAA satchel / Book of Skills reveal: live 3D capture, 5 beats, post-process blur, dust, sounds (replaces #231) | `handoffs/reveal-aaa-268` |
| #11 | #272 | Survivors: wounded soldiers arrive when it is calm, E takes one in, he heals 60 s, then becomes a soldier | `handoffs/survivors-11` |
| #226 | #275 | Weather v1: daily roll plus forecast, rain curtain, fog through BP_DayNight, storm wind, lightning, grade | `handoffs/weather-226` |
| #277 | #278 | Crossbow flares: barracks upgrade (F), flares only at spotted threats at night | `handoffs/flares-277` |
| #224 | #282 | Castle upgrades: walls (colossus breach ×1.75 / ×2.5) and tower ballistas (J / K) | `handoffs/castle-upgrades-224` |
| #283 | #285 | Cannon scroll map: parchment map, click where the cannon goes; new cannons movable, starters locked | `handoffs/cannon-map-283` |
| #157 | #286 | Realm screen distortion v2: no volume to place, fades in when you enter | `handoffs/realm-157` |
| #185 | #289 | Medics: barracks (M), heal soldiers and the hero, HUD line | `handoffs/medics-185` |

**Paste order for the HUD hook chain in BPC_MotionFX:**
1. #269 (the v2 graph);
2. #285 (`manifest_motionfx_map.json`);
3. #289 (`manifest_motionfx_medics.json`);
4. #141's add-on still applies on top.

**Barracks keys added (no BarracksHUD re-paste):** F flares, J walls, K towers, M medics. O at the artillery yard opens
the #283 map.

**Owner rules learned today:** an owner message starting with `W:` is a whiteboard task (AGENTS.md rule 6). Take cards
one after another without asking. Characters stay stand-ins until the MetaHuman pass.

**Follow-ups noted on the cards:**
- zombies target survivors and medics;
- rain douses torches;
- crossbow storm spread;
- the wetness layer (needs the owner's before/after OK);
- wall mesh variants for #224 (TGA);
- the #283 in-engine screenshot.

### adjustedfilm, 2026-10-31 afternoon (added before context ran out)

| Card | Hand-off | Where | State |
|---|---|---|---|
| #292 muddy footprints (owner W:) | #298 | `handoffs/mud-prints-292` | waits on the Master; first Play check: prints sideways -> `MI_MudPrint` Swap = 1 |
| #295 nightfall scroll looks plastic (W:) | filed | `handoffs/scroll-295` | one script, M_NoticeBanner rebuilt in place (backup kept), no BP paste |
| #293 blobs / mines / realm realism (W:) | part 1 filed | `handoffs/blob-realism-293` | research done; realm bubble v3 (apply only after owner OK); **part 2 flesh-slime waits on the material export request**, spec in RESEARCH.md §3 |
| #302 Multi-User editing across PCs | kit | `handoffs/multi-user` | owner runs `check_pc.ps1` on each PC and picks seats; this laptop is NOT a seat (2 GB VRAM, 58 GB free) |
| #296 / #297 cave texturing + dungeon teleport (W:) | - | - | assigned to laptop2, not started |
| #294 realm bounces cannonballs (W:) | TGA #299 | `handoffs/realm-284` | TGA |

- **New owner rule: `AR` = "according to our studio office rules"** (AGENTS.md rule 6), next to `W:` = card first.
- TGA's queue (set 2026-10-31): #294 done, #225 art done, #279 staircases in progress.

### adjustedfilm, 2026-10-31 midday session

| Card | Hand-off | Where | State |
|---|---|---|---|
| #266 PRIORITY infection cure | #307 | `handoffs/antidote-266` | Antidote at Vesna (the missing #148 step 5): APOTHECARY panel drawn by BP_NoticeHUD, 108-node paste + 4 links + icon import; dry-run merge OK on the 10-30b NoticeHUD export |
| #297 cave door (W:) | see cafeteria (part 1) | `handoffs/cave-296-297` | BP_CaveDoor pair, [E] fade + teleport; part 3 (sub-level + placing) waits on request #308 (cave dump) and TGA's #309 |
| #309 mine dungeon art kit | - | card for TGA | tunnels, timber supports, mine chamber, mine door |
| #296 cave texturing (W:) | - | - | claimed; waits on request #308 (`dump_cave_ue.py`, read-only) |

Still waiting: #228 report (`handoffs/walltops-228/walltops228_report.txt`), #293 part 2 (request #304), #183 (request #291).
#213 part 2 ("UNLOCK - 2 PTS" boxes): the text is in **no** Blueprint export (searched every export for UNLOCK / PTS /
{0}), so it comes from a widget, a material or a texture. It needs an editor search (checkking's card).
Lesson: `from bpkit import *` overwrites `HERE`. Set it again after the import, or the outputs land in tools/laptop2/bpgen.
