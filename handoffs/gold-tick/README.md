# Gold number ticks up (TGA1's spec, chat 487 + 541; built by i5 / adjustedfilm, 2026-11-02)

The visible gold is drawn in **BP_SkillTreeHUD**: `CX_1882` (Gold) → `CX_1883` Conv_IntToString → digits (15
M_UI_GoldDigits draws). Today it jumps. With this, the number counts smoothly to the new value (FInterpTo, speed 8:
~90 % of the way in 0.3 s), also while the game is paused (shop). **Only `CX_1883.InInt` changes**; the shop's money
checks (`CX_778` etc.) keep reading the real Gold.

## Files
| File | What |
|---|---|
| `gen_goldtick.py` | generator (run with UE's Python: `Engine/Binaries/ThirdParty/Python3/Win64/python.exe -I`) |
| `build/BPC_GoldTick_graph.txt` | EventGraph of the new component: BeginPlay sets Shown = ShownInt = Gold; Tick interpolates (17 nodes) |
| `build/SkillTreeHUD_GoldTickHook_graph.txt` | 3 nodes for BP_SkillTreeHUD: Self → GetComponentByClass(BPC_GoldTick) → ShownInt (`GtHookShownInt`) |
| `setup_goldtick_ue.py` | creates BPC_GoldTick (vars Shown double, ShownInt int; tick even when paused), backs up BP_SkillTreeHUD → `BP_SkillTreeHUD_BACKUP_GT`, adds component "GoldTick" |
| `rewire_goldtick_ue.py` | `CX_1883.InInt` ← `GtHookShownInt.ShownInt`, compile, save; `--revert` puts `CX_1882.Gold` back |

Pre-checks: `applyall check` → Validation OK on both graphs; `fix_impure.py` → no changes on both. i5 dry runs on the
live session (14:33): setup would create + add; rewire finds CX_1882 / CX_1883 (the hook node exists after the paste).

## Apply (i9)
1. `py "<repo>/handoffs/gold-tick/setup_goldtick_ue.py" --dry-run`, then without `--dry-run` (saves BPC_GoldTick and BP_SkillTreeHUD: post 'saving').
2. Open BPC_GoldTick → EventGraph → paste `build/BPC_GoldTick_graph.txt` → Compile, Save.
3. Open BP_SkillTreeHUD → EventGraph → paste `build/SkillTreeHUD_GoldTickHook_graph.txt` (anywhere).
4. `py ".../rewire_goldtick_ue.py" --dry-run` (3 × found), then without → compiled + saved.

## Checks (Play)
- [ ] At start the gold shows the real amount (no count-up from 0).
- [ ] Kill / pick up gold: the number rolls up smoothly to the new total.
- [ ] Buy at Vesna (game paused): the number rolls down smoothly; the purchase itself used the real gold.
- [ ] 0 new runtime errors.
Undo: `rewire_goldtick_ue.py --revert` (the component can stay, it only reads).

Not in this hand-off: TGA1's soft plate behind the digits and the level-up banner / wave label (next).
