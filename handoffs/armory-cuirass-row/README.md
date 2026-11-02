# Hide the lone cuirass on Vesna's WEAPONS rack (i5 / adjustedfilm, 2026-11-02, i9's queue item 2)

i9's ruling (chat 473): hide the old single "Obsidian Sovereign Cuirass" entry in BP_ArmoryHUD's WEAPONS rack; the
Obsidian Torso bundle (#424) replaces it. Keep the 3D chest piece on the showcase.

## How the rack works (11-01 export)
A carousel over MPC `Shop.G` = 0..4: 0 Noble Crossbow, 1 Golden Breastplate, 2 Golden Sovereign, 3 Knight's Great Helm,
4 Obsidian Sovereign Cuirass. Up/down (`CX_1996` / `CX_2007` set Shop) wrap with `> 4.5 → 0` and `< -0.5 → 4`.

## Fix: 3 pin defaults, no links, no nodes (`fix_cuirass_row_ue.py`)
| Pin | Was | Now |
|---|---|---|
| CX_1988.B (wrap going down) | 4.5 | 3.5 |
| CX_2001.B (wrap going up) | 4.5 | 3.5 |
| CX_1993.B (wrap target from -1) | 4.0 | 3.0 |

The script checks each current value first and changes nothing if one differs. i5 dry run on the live session (11:2x):
all three "ok".

## Apply (i9)
1. `py "<repo>/handoffs/armory-cuirass-row/fix_cuirass_row_ue.py" --dry-run` → 3 × ok.
2. `py ".../fix_cuirass_row_ue.py"` → sets, compiles, saves BP_ArmoryHUD (heavy save: post 'saving' first).
3. Undo: `--revert`.

## Checks (Play)
- [ ] WEAPONS rack: up/down cycles Crossbow → Breastplate → Sovereign → Great Helm → Crossbow; the cuirass never shows.
- [ ] Going up from the Crossbow lands on the Great Helm.
- [ ] Buying each of the 4 still works; the Obsidian Torso bundle still shows its chest preview.
- Note: a game already sitting on the cuirass (Shop.G = 4) shows it until the next up/down; new games start at 0.
