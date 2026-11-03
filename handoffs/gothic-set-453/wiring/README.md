# #453 Gothic set wiring (i5, 2026-11-03): status and parts

Built on i9's fresh export `handoffs/exports/adjustedfilm/gothic-453/BPC_ObsidianSet.t3d.txt` (09:02, v3 live).
**Not handed to the Master yet:** this goes out as ONE hand-off with the Vesna rows and the hero pieces (below), so the
Master gets a finished feature, not an inert graph.

## Design (Decision on card #453)
- Gothic is a **second set on the same component** (`BPC_ObsidianSet` v4), not a new component.
- Parts = piece ids 21..31 = bits 11..21 of the same `ObsOwned` / `ObsWorn` masks. The save format is unchanged.
- Bundles 4..7 = Gothic Helm / Torso / Gauntlets / Legs (Obsidian stays 0..3, so Vesna's v3 indices keep working).
- **One set per slot:** wearing or buying bundle B first takes off bundle (B + 4) % 8. The Gothic torso going on also
  takes the Obsidian cuirass (MPC Armor) off.
- **Tiers per set:** Obsidian unchanged (BundleCount, ObsSet.A, burst, shockwave). Gothic: GothicCount -> GTier,
  DR -2 / -5 / -8 / -12 %. Total DR = Obsidian tier DR + Gothic tier DR. It stays at or below 0.15, because at most 4 bundles are worn.
- Knight slots hide when all Obsidian (`KnightCover`) or all Gothic (`KnightCover2`) pieces covering them are worn.
- Prices: 80 % of the Obsidian part. Bundles: Helm 120, Torso 552, Gauntlets 128, Legs 320.

## Files
| File | What |
|---|---|
| `gen_set_v4.py` | generator: fork of `obsidian-bundles-424/gen/gen_set_v3.py` (v3 regenerates byte-identical except GUIDs); `#453` comments mark every change |
| `BPC_ObsidianSet_v4_graph.txt` | 886 nodes, 1150 links. `fix_impure`: no change. `applyall check`: **Validation OK**. Variables: everything in the live export + GothicCount, GTier, KnightCover2 |
| `setup_gothic_ue.py` | DRY_RUN default; backup `BPC_ObsidianSet_v3_backup`, adds the 3 variables, extends the data 4/11 -> 8/22 (re-run safe). The dry run on i5 is all ok (`setup_gothic.txt`) |
| `read_set_cdo_ue.py` / `set_cdo.json` | read-only dump of the live class defaults |

## Still to do (in order)
1. **Vesna rows** (`BPC_VesnaTrade`): 4 Gothic bundle rows, Gothic tier box, doll icons on the #424 pattern
   (`obsidian-bundles-424/gen/gen_trade_bd.py`). Waits for TGA1's #446 Vesna pastes (cursor fix + WEAPONS tab), then
   a fresh export (agreed in the fast chat, line 955), so the two whole-graph pastes don't overwrite each other.
2. **Hero pieces** (`setup_gothic_pieces`): when TGA1's 11 meshes land under
   `/Game/CastleDefender/Characters/Hero/Armor/LandshutGothic/`: add StaticMeshComponents tagged `ObsK21..31` to the hero,
   then append PieceId / PieceBone / PieceOffset rows (L/R pairs; also cuirass/spine, sallet/head and doublet/spine_03),
   with ref-pose offsets measured like `obsidian-set-v2`. Then set the Gothic bits in AvailMask. Until then the Gothic rows show FORGING.
3. **Phase 2** (needs BP_ThirdPersonCharacter + BPC_WeaponKit exports): Gothic move speed +3/5/7/10 %, stamina regen
   (tier 3), Helmschmid's Edge +10 % sword damage (4/4).

## Apply order for the Master (when 1 and 2 are ready)
1. `setup_gothic_ue.py` dry run, then `DRY_RUN = False`.
2. Paste `BPC_ObsidianSet_v4_graph.txt` into BPC_ObsidianSet's EventGraph (Ctrl+A, BackSpace, Ctrl+V), Refresh All
   Nodes, Compile, Save.
3. Vesna graph + pieces (their own READMEs).

**Play checklist (later):**
- Buy Gothic Torso while wearing Obsidian Torso: the Obsidian torso and cuirass come off and Gothic goes on.
- Tier box: 2 Gothic + 2 Obsidian shows DR -11 %.
- Save, quit and reload: the same pieces are worn.
- DebugGiveAll wears Obsidian only.
