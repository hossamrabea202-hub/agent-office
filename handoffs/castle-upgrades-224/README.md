# #224 Castle upgrades v1: walls and towers, bought with gold + mine ore

By `adjustedfilm (Claude)`, 2026-10-31.
- **The gate track already exists:** the forge's gate bands (#208, `ForgeGate`, up to +150 % gate life). This card adds
  the **walls** and **towers** tracks.
- **Built on** `handoffs/exports/master/2026-10-30b`:
  - BP_ZombieWallBreaker: smash `SM_Dmg`, 500 damage on a BP_WallBreachSpot;
  - BP_ZombieHUD `Gold` + `Ore[5]` (#201);
  - BP_NoticeHUD `PushNotice`;
  - BP_CastleSave;
  - laptop2's FireBallista kit (#10).
- **Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** on all graphs:
  - `BPC_CastleUpgrades`: 211 nodes;
  - `BP_TowerBallista`: 126 nodes;
  - the wall-breaker paste: 9 nodes.
  - The **BP_ZombieWallBreaker merge dry-run on the live export is OK** (+10 links, 1 rewire).

## What the player sees

At the barracks NPC a notice offers the next level of each track:

> Castle works – [J] Walls: Reinforced masonry: 300 gold, 6 iron     [K] Towers: Ballista nests: 400 gold, 6 iron, 2 copper

| Track | Level | Cost | Effect |
|---|---|---|---|
| Walls | 1 Reinforced masonry | 300 gold + 6 iron | a colossus needs **×1.75** the smashes to breach a wall |
| Walls | 2 Iron-banded walls | 700 gold + 8 iron + 3 silver | **×2.5** |
| Towers | 1 Ballista nests | 400 gold + 6 iron + 2 copper | every placed tower ballista appears and fires: nearest zombie within 50 m, a colossus first; 120 damage every 4 s |
| Towers | 2 Fire ballistas | 900 gold + 6 iron + 2 gold ore | 180 damage every 2.5 s, brighter coals |

- **J** buys walls and **K** buys towers. Both are saved.
- Messages:
  - *"Walls built: Reinforced masonry."*
  - Too poor: *"Not enough: walls needs …"*
  - At the top: *"Your walls are already at their best."*
- **The ballista:** it yaws onto the target, thwacks (sound), and the spear flies in a 0.35 s arc. The hit deals real
  `ApplyDamage`, so it kills and gives XP like any other damage. The brazier coals glow with a real flickering light.

## How it works

- **`BPC_CastleUpgrades`**, the hero component "CastleUpgrades":
  - loads `CastleSaveCastle` (Data = [Walls, Towers]);
  - `UpgPoll` (1 s) shows the barracks offer once per visit;
  - `UpgKeys` (0.05 s, edge-detected J / K):
    - checks the gold and the ores (`Ore[0]` iron, `[1]` copper, `[2]` silver, `[3]` gold ore);
    - takes the payment and raises the level;
    - saves and shows a notice.
- **Walls:** the 9-node paste in BP_ZombieWallBreaker feeds `SM_Dmg.BaseDamage`
  = 500 / (1 + 0.75 × Walls). It reads the level from the hero's component, and stays 500 if the component is missing.
- **`BP_TowerBallista`** (Think, 0.05 s):
  - hidden until Towers ≥ 1;
  - picks the best zombie in range, aims the Frame (yaw), shoots;
  - flies the Spear and hits;
  - puts the Spear back on the Frame;
  - flickers the coals.

## Files

| File | What |
|---|---|
| `setup_castle224_ue.py` | Editor script, safe to re-run, with `--dry-run`. Makes BPC_CastleUpgrades (and adds it to the hero), BP_TowerBallista from the FireBallista meshes, and SFX_Ballista_Shot. |
| `VARIABLES_BPVar.txt` | 5 BPVar lines for BPC_CastleUpgrades and 10 for BP_TowerBallista (`VARIABLES.md`). |
| `BPC_CastleUpgrades_graph.txt`, `BP_TowerBallista_graph.txt` | the new EventGraphs |
| `WallBreaker_Walls_graph.txt` + `manifest_wallbreaker.json` | the walls effect in BP_ZombieWallBreaker (applyall merge) |
| `gen_castle224.py` | generator (bpkit) |
| `assets/adjustedfilm/Castle224/` | `sfx/SFX_Ballista_Shot.wav`, `source/make_ballista_sfx.py` |

## Steps (Master: paste only)

1. **Prerequisite:** if `/Game/CastleDefender/Weapons/FireBallista` is missing, run
   `py "<repo>/assets/laptop2/FireBallista/import_kit_ue.py"`.
2. **Run the setup.** Dry-run first: `py "<repo>/handoffs/castle-upgrades-224/setup_castle224_ue.py" --dry-run`. Then run it
   without `--dry-run`.
3. **Add the variables.** Paste the BPVar lines on BPC_CastleUpgrades (5) and BP_TowerBallista (10), then Compile each.
4. **Paste the graphs.**
   - Paste `BP_TowerBallista_graph.txt` into BP_TowerBallista, then `BPC_CastleUpgrades_graph.txt` into
     BPC_CastleUpgrades. Compile and Save both, then the hero.
   - **Walls:** export BP_ZombieWallBreaker's EventGraph to `live.t3d`, then run
     `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/castle-upgrades-224/manifest_wallbreaker.json --out merged.t3d`.
     Then Ctrl+A, Delete, paste `merged.t3d`, Compile and Save.
5. **Place the ballistas.** Place **2–4 BP_TowerBallista** on the tower tops or wall corners that overlook the field, and
   Save the level.
   - They stay invisible until the Towers upgrade is bought, so placing them changes nothing until then.
   - Rotation doesn't matter: they aim themselves.

**Faster test:** give yourself 2000 gold and set `Ore` to 20 each on the HUD. Buy both tracks (J J K K at the barracks).

## Checks (Play)

1. **The barracks offer:** the notice shows the next levels and costs. J or K with too little: the "not enough" notice.
   With enough: gold and ores go down, the "built" notice shows, and the next offer moves up. Level 2 is the top.
2. **Towers 1:** the placed ballistas appear. With zombies within 50 m they aim, thwack and fire a flying spear every
   4 s, and the zombie takes the hit. A colossus is chosen first.
3. **Towers 2:** every 2.5 s, harder hits, brighter coals.
4. **Walls:** time a colossus breach at level 0 and then at level 2. It takes about 2.5× as many smashes.
5. Save, then load: both levels kept.
6. No "Accessed None" from BPC_CastleUpgrades, BP_TowerBallista or BP_ZombieWallBreaker.

## Decisions

- **Gate = the existing forge gate bands** (#208). I didn't add a second gate track.
- **Prices:** walls 300 / 700 gold plus iron (and silver for level 2); towers 400 / 900 gold plus iron, copper and gold
  ore. Iron is the common ore and gold ore the rare one, so level 2 is a long-term goal, as the card asks.
- **No visible wall change yet:** the wall meshes stay the same. Showing the levels on the castle needs new wall mesh
  variants (decal rule: no live-material edits), which is art for TGA. Only the ballistas appear in v1.
- **Damage and repair states between waves:** not in v1. BP_WallBreachSpot isn't in an export, so I can't read its HP;
  that is a follow-up once it is exported.
- **Ballista placement is a Master step** (2–4 actors). The tower-top positions aren't in any export, so I can't place
  them by script.
- **Keys J and K at the barracks**, so the big BP_BarracksHUD needs no re-paste. Same approach as the flares (#277, F).

## Office rules applied

- **The Master only pastes:** a setup script with a dry-run, BPVar lines, clean graphs, a dry-run merge on the live
  export, steps and tests.
- **Industry secrets rule 6:** the coals light at 1900 K with a slow two-sine flicker, from a real light.
- **Decals and live materials:** untouched. The FireBallista meshes and material are reused as they are.
