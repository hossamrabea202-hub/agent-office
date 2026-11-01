# laptop-i5 as second editor (UE 5.8.4), #399

Checklist status: see the READY reply on #399.

## Low settings (step 4)
Copy both files in `WindowsEditor/` into `<Castle Defender 5.8>/Saved/Config/WindowsEditor/` **before the first open**.
They are local editor files only. Lookdev and screenshots for judging still use locked exposure in a test level;
for those, raise `r.ScreenPercentage` to 100 in the console for the shot.

## First jobs (step 6), my own test levels only
1. `/Game/_Laptop/WK_Test` (new level). `py <repo>/handoffs/winter-map/ue/winterkeep_ue.py --dry-run`, then
   `--step assets`, then `--step meshes` (FBX import now switches Interchange off for the run and restores it).
2. #397 weapons, by TGA's hand-off steps, into new folders only.

Never save ThirdPersonMap, BP_ThirdPersonCharacter, the HUD chain or other shared Blueprints. Work returns as new assets
plus scripts.
