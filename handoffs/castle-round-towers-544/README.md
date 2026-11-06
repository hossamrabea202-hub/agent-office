# #544 Round back towers (adjustedfilm, 2026-11-06)

Owner: "i want the back towers of the castle to be circular also, you can duplicate the existing ones and reposition and use them, then give the handoff to i9".

## What it does (`round_back_towers_ue.py`, level actors only)

- **Copies** every piece of the two round front towers, 487 actors on the i5 copy, to the back corners. Folders: `Castle/TowerBack_A` and `_B`, labels `BackTower_*`.
- **Places them where the walls cross:** back-left at (4600, 50) turned +90, back-right at (4600, 3315) turned -90. The bailey's north wall is at Y 3315, not 3450, so the back is not a plain mirror of the front.
- **Hides, never deletes:** the square `Castle_BaileyTower*` stacks and loose slabs and trims inside the new drums, 71 actors, with collision off. This includes the old stair `Stair279_04` and `StairRamp_03`, which would run into the back-right drum.
- **Moves** the back-right rooftop cannon 4.3 m along -Y, off the new stair well.

**Decision:** "back towers" means the two rear corners. The two square `Castle_CornerTower`s at X 2950, midway along the sides, stay square. Tell me if those should be round too.

The new drums are 12 m across; the old squares were 4.3 m. So the back of the castle will look noticeably heavier, matching the front.

## Steps (Master, editor idle, not in Play, main level open, castle loaded)

1. `git pull`.
2. `py handoffs/castle-round-towers-544/round_back_towers_ue.py --dry-run`. Expect about 490 pieces, about 70 hidden, 1 cannon to move. It stops if `Tower9_A_Drum` or `_B_Drum` is missing.
3. Run it with no flags. Save the level. **Rebuild navigation.**
4. Post a screenshot of the back of the castle on #544: I could not take any here.
5. Play.

Revert: `--revert` on the same PC (it reads `back_towers_backup.json`), save the level, rebuild navigation.

## Tests in Play

- Both new doorways line up with their two wall walks. Walk through them both ways.
- Soldiers and crews reach both rooftop cannons through the new stairs. **This is the main risk**, because the old stair is hidden and the navigation changes.
- Both cannons sit correctly on the roof, aim and fire, and the moved one is not clipping the parapet.
- Nothing pokes into the chambers, and the outside has no gaps where wall meets drum. `CastleStones` batches are not hidden, so check for stones inside the drum.
- Torch flames: only the torch meshes are copied. If the front torches get their flames from separate actors, the back ones will be unlit.
- Grime and contact decals on the drums look right after the turn.

## Tested, and not tested

On the i5 project copy, GUI editor, never saved: dry-run; apply (487 copies, 71 hidden, 1 cannon moved); second apply refused; revert (487 removed, 71 shown, cannon back, actor count back to 4273). Measured: the doorways sit on the wall lines at walk height (z 681 to 974), both drums at z 0 to 1050.

**Not tested: nobody has seen it.** Screenshots hang the editor on this laptop, so the look is unchecked. It has not run in Play. The copy is older than the live level, so counts may differ and any actor moved or added at the corners since 11-04 is unchecked.

## Rules applied

Reuses existing calibrated assets and materials, with new actors only and no material touched. Knowledge base 5 (grounded). INDUSTRY_SECRETS 0.10.
