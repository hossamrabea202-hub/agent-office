# #185 Medics: recruit at the barracks, they heal your soldiers and you, and never fight

By `adjustedfilm (Claude)`, 2026-10-31.
- **Builds on:**
  - BP_SoldierSword: HP in `State.X`, alive while `State.Z` < 0.5 (as #41 reads it);
  - the hero's `DamageTaken` (BP_ThirdPersonCharacter, 10-30b);
  - BP_ZombieHUD `Gold` and BP_NoticeHUD `PushNotice`;
  - TGA's medic gear (#248);
  - the BPC_MotionFX HUD hook (#269 → #283).
- **Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK**:
  - BPC_Medics: 95 nodes;
  - BP_Medic: 137 nodes;
  - the HUD paste: 5 nodes.
  - **The BPC_MotionFX merge dry-run is OK** on the v2 graph with the #283 map merge already applied.

## Numbers (the card asked for them first)

| | |
|---|---|
| Price | 150 gold, at the barracks NPC with **M** |
| Limit | 4 medics |
| Healing | 8 HP/s (4 every 0.5 s) within 2.5 m |
| Looks for patients | within 25 m: the most wounded soldier, or the hero |
| Retreats | a zombie within 6 m → runs to the hero |
| Otherwise | follows the hero, 4 m behind |
| Walk speed | 380 |

## What the player sees

- **At the barracks NPC:** *"[M] Recruit a medic: 150 gold. Medics heal your soldiers and you, and never fight. (n/4)"*.
  M buys one; he walks out of the barracks wearing TGA's satchel and herb-sprig armband.
- **In battle:** medics move to the most wounded soldier, or to you, stop beside him and heal. A green **+ HEAL** floats
  over the medic while he works. If zombies come within 6 m, he runs back to you.
- **HUD:** **MEDICS n / 4** under the top-left HUD block, shown only while you have medics.

## How it works

- **`BPC_Medics`**, the hero component "Medics":
  - counts the medics every second;
  - shows the barracks offer once per visit;
  - M (edge-detected) checks the limit and the gold, pays and spawns a BP_Medic beside the NPC;
  - `DrawMedics` draws the HUD line.
- **`BP_Medic`:**
  - **BeginPlay:** attaches the satchel to `spine_03` (or `Spine2`) and the armband to `upperarm_l` (or `LeftArm`),
    whichever the skeleton has.
  - **Think** (0.5 s):
    1. checks for danger;
    2. picks the patient: the soldier with the biggest wound (the gap between his highest HP seen and his HP now), or
       the hero if his `DamageTaken` is bigger;
    3. acts: run, follow, walk to the patient, or heal: soldier `State.X` + 4 (capped at his max), hero `DamageTaken` − 4
       (floored at 0).
- **HUD:** a 5-node paste in BPC_MotionFX that runs after the #283 map draw.

## Files

| File | What |
|---|---|
| `setup_medics185_ue.py` | Editor script, safe to re-run, with `--dry-run`. Makes BP_Medic (soldier stand-in body, Satchel, Armband, HealFX) and BPC_Medics, and adds "Medics" to the hero. |
| `VARIABLES_BPVar.txt` | 5 BPVar lines for BPC_Medics and 9 for BP_Medic (`VARIABLES.md`). |
| `BPC_Medics_graph.txt`, `BP_Medic_graph.txt` | EventGraphs |
| `MotionFX_Medics_graph.txt` + `manifest_motionfx_medics.json` | the HUD line (BPC_MotionFX merge, after #283's) |
| `gen_medics185.py` | generator (bpkit) |

## Steps (Master: paste only)

1. **Medic gear:** if `/Game/CastleDefender/Characters/NPC/MedicGear` is missing, run
   `py "<repo>/assets/tga/MedicGear/import_medicgear_ue.py"` (TGA #248).
2. **Run the setup.** Dry-run first: `py "<repo>/handoffs/medics-185/setup_medics185_ue.py" --dry-run`, then run it
   without `--dry-run`.
3. **Add the variables:** BPVar lines on BPC_Medics (5) and BP_Medic (9), then Compile each.
4. **Paste the graphs:** `BP_Medic_graph.txt` into BP_Medic first, then `BPC_Medics_graph.txt` into BPC_Medics. Compile
   and Save both, then the hero.
5. **HUD line (after #285):** export BPC_MotionFX's EventGraph, then merge `manifest_motionfx_medics.json`. Paste,
   Compile and Save.

## Checks (Play)

1. At the barracks: the offer shows once per visit. M with ≥ 150 gold: a medic walks out with the satchel and armband,
   gold goes down 150, and MEDICS 1 / 4 appears. A fifth M gives the "all the medics" notice. Too poor: the "not enough
   gold" notice.
2. **Let soldiers get hurt:** the medic walks to the most wounded one, + HEAL shows, and his HP climbs at about 8/s,
   stopping at his full HP.
3. **Get hurt yourself:** the medic comes to you and heals (DamageTaken goes down to 0).
4. **A zombie comes close:** the medic runs to you and doesn't fight.
5. Nobody hurt: he follows you.
6. No "Accessed None" from BP_Medic or BPC_Medics.

## Decisions

- **"Child of soldier" from the card wasn't used.** BP_Medic is a plain Character with the soldier's body. A child of
  BP_SoldierSword would be counted, ordered, targeted and made to fight by the army code, and medics must never fight.
- **Recruiting is at the barracks NPC with M**, not on a new barracks card. That avoids re-pasting the big
  BP_BarracksHUD; same approach as #277 / #224.
- **A soldier's max HP is the highest HP the medic has seen on him.** There is no max-HP variable on the soldier. New
  recruits start full, so this matches in practice.
- **Zombies don't target medics in v1.** Medics stay behind the hero and run from zombies within 6 m. A zombie-target
  hook (like TGA's farmer raid #223) can come later.
- **No bandage animation in v1:** he stops and the "+ HEAL" shows. A kneel or bandage montage comes when an animation
  set is chosen (the MetaHuman pass).
- **Medics aren't saved across a load,** the same as #230's ordered cannons.

## Office rules applied

- **The Master only pastes:** a setup script with a dry-run, BPVar lines, clean graphs, a chain-tested merge, steps and
  tests.
- **Characters:** a stand-in soldier body until the MetaHuman pass (owner rule). TGA's licence-safe herb-sprig emblem,
  not a red cross.
