# #267 texture cut: re-import plan (i5 / adjustedfilm, 2026-11-02, i9's queue item 7, list only)

TGA's #262 pass already shrank **307 source textures** in the repo (same file names). The saving only reaches the game
(and the weak laptops' GPU / RAM) once the textures are **re-imported in UE**. Nothing is imported yet by this plan.

## Order (by GPU memory saved, from `audit.json`)
| # | Kit | Textures | Saves |
|---|---|---|---|
| 1 | checkking/Weapons | 101 | 228 MB |
| 2 | checkking/Obsidian-Sovereign | 15 | 160 MB |
| 3 | laptop2/CampKit | 58 | 152 MB |
| 4 | laptop2/WeaponPack | 16 | 146 MB |
| 5 | laptop2/SiegeBarricadeKit | 12 | 128 MB |
| 6 | laptop2/FloraKit | 33 | 84 MB |
| 7 | tga/SiegeEngines | 6 | 64 MB |
| 8 | laptop2/FireBallista | 7 | 51 MB |
| 9-12 | tga/RealmCrack, Feast, HalfHorseZombie, RealmWasp | 19 | ~196 MB |
| 13-28 | 16 small kits (BarracksProps, OreShed, SiegeGate, Signs, ...) | 40 | ~203 MB |
| | **total** | **307** | **~1,412 MB** |

The top 6 kits are 1,0 GB of the 1,4 GB.

## How (one kit per run, small steps)
1. `py "<repo>/handoffs/texture-plan/reimport_downsized_ue.py"` — **dry run**, read-only: matches each shrunk PNG to its
   UE texture by the texture's import source path, writes `reimport_list.txt` (done / TODO / NO UE TEXTURE per file).
2. Per kit, in the order above: `... --apply --kit checkking/Weapons --limit 40` (repeat until the kit shows no TODO).
   Re-import keeps each texture's settings (compression, sRGB, LOD group); same asset, so no material or mesh changes.
3. After each kit: a look at one prop of the kit in the level (at game distance it should match; TGA's before/after
   sheets are on SCREENSHOTS).

## Open (owner decisions from TGA's README, still unanswered)
- Confirm "large structures stay 2K" and the 5 E1 props at 2K.
- Who runs it: i9 (GPU, fast) or i5 one kit at a time. Re-importing on i5 also lowers i5's own memory pressure.
- Textures the dry run reports as "NO UE TEXTURE" were imported from another path (e.g. a kit's temp folder): those need
  the kit's own import script instead (`assets/<owner>/<kit>/import_*_ue.py`).
