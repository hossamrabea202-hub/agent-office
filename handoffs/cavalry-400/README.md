# #400 Stables, horses, knights, heavy cavalry (checkking (Claude), 2026-11-01)

Owner's order: "W: stables, horses, knights, heavy cavalary". Cards: #401 stables, #402 destrier, #403 knight kit,
#404 heavy cavalry gameplay. Research: [`RESEARCH.md`](RESEARCH.md). Gameplay design and numbers: [`GAMEPLAY.md`](GAMEPLAY.md).

| Card | Delivered | Hand-off |
|---|---|---|
| #401 | `assets/checkking/Cavalry/Stables` (SM_Stable + 6 tiling sets + `import_stable_ue.py`) | #405 |
| #402 + #403 | `assets/checkking/Cavalry/Destrier`, `Knight` + `import_cavalry_ue.py` | #406 |
| #404 | this folder: BP_Cavalry + BPC_Cavalry | (this hand-off) |

## #404 Heavy cavalry: what the player gets

- **At the stables** (any actor with the tag `Stables`, i.e. the #401 building once placed) **or at the barracks NPC**
  until then: *"[L] Raise a knight on a barded destrier: 400 gold. Heavy cavalry charges zombies with the lance. (n/4)"*.
  **L** buys one: a knight on a yellow-caparisoned destrier rides out.
- Up to **4 knights** ride in a line 8 m behind you. When a zombie comes within 35 m they **charge**: speed builds to a
  full gallop, the lance comes down (couched across the neck), they hit the first zombie hard (knocked flying), trample
  the ones beside it, **ride straight through**, wheel back to you, rest 3 s and charge again.
- Lances break (30 %); the knight gets a fresh one back at your side.
- **Weakness:** a knight that slows down inside a crowd (4+ zombies within 3 m) is bogged and loses 30 HP/s. Don't let
  them stand in the mob.
- Death: the horse falls, "A knight has fallen.", gone after 12 s.

## Pre-checked

- `gen_cavalry404.py` builds the graphs with bpkit (the #185 medics pattern).
- `tools/applyall/fix_impure.py` on both graphs: **nothing to change** (every GetAllActorsOfClass / GetActorOfClass /
  cast is already on the exec chain; the HUD cast has one consumer).
- `applyall check`: **Validation: OK** — BP_Cavalry 437 nodes / 476 links, BPC_Cavalry 90 nodes / 101 links.
- New Blueprints only. The one change to an existing asset: the hero gets a "Cavalry" component (like "Medics").

## Steps (Master: paste only)

1. **Assets first** (hand-off #406): `py "<repo>/assets/checkking/Cavalry/import_cavalry_ue.py" --dry-run`, then without.
2. **Setup:** `py "<repo>/handoffs/cavalry-400/setup_cavalry404_ue.py" --dry-run`, then without `--dry-run`.
   It makes BP_Cavalry (horse Mesh, Tack / Lance / RiderLegs / Rider) and BPC_Cavalry, and adds "Cavalry" to the hero.
3. **Variables:** paste the lines of `VARIABLES_BPVar.txt` one at a time on the VARIABLES header of My Blueprint:
   23 on **BP_Cavalry**, 7 on **BPC_Cavalry**. Compile each.
4. **Graphs:** `BP_Cavalry_graph.txt` into BP_Cavalry's EventGraph (Ctrl+A, Delete, Ctrl+V), Compile, Save. Then
   `BPC_Cavalry_graph.txt` into BPC_Cavalry, Compile, Save; Compile and Save the hero.
5. **If a node comes in red:** right-click → Refresh Node, Compile. The ones built without a template:
   `SetLeaderPoseComponent`, `HideBoneByName`, `SetMaterialByName`, `SetPlayRate`, `ApplyDamage`, `LaunchCharacter`,
   `Normal2D`.

## Checks (Play)

1. At the barracks NPC (or the tagged stables) the offer shows once per visit. **L** with ≥ 400 gold: a mounted knight
   appears beside it, gold −400, notice "A knight rides out…". A fifth L: "All four knights…". Too poor: "Not enough gold…".
2. **Look:** the horse stands on the ground (not floating, not sunk), yellow caparison with black eagles, the mane is
   hidden under the neck cover, the soldier's upper body sits in the saddle with the mail legs in the stirrups, lance
   upright. If the rider floats or sinks: change `RiderDrop` (default −92 cm) in BP_Cavalry's Class Defaults.
3. Walk around: the knights follow 8 m behind in a line, walking / trotting / galloping to keep up (no foot sliding
   beyond ±20 %).
4. Let a wave come: a knight gallops at the nearest zombie, the lance drops to couched, the zombie is thrown on impact
   (metal hit sound), zombies beside it are knocked aside, the knight rides on ~14 m, turns back to you, then charges
   again after ~3 s. Sometimes the lance disappears (broken) and comes back at your side.
5. Lead a knight into a big crowd so it stops: it loses HP and eventually falls (death anim, notice).
6. No "Accessed None" from BP_Cavalry or BPC_Cavalry in the log.

## Tune by eye (Class Defaults of BP_Cavalry)

`RiderDrop` (rider height in the saddle), `ChargeSpeed` 950, `LanceDmg` 140, `TrampleDmg` 35, `Acquire` 3500 cm,
`BogDPS` 30, `MaxHP` 600. Price / limit on BPC_Cavalry: `Price` 400, `MaxKnights` 4.

## Office rules applied

The Master only pastes (setup script with dry-run, BPVar lines, clean pre-checked graphs, steps, tests); new assets
only; INDUSTRY_SECRETS 3.4 (play rate within ±20 %, speed picks the clip); research before design.
