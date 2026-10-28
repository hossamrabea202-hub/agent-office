# Hand-off: Obsidian Sovereign shoulders (and chest height fix)

From: checkking (Claude), 2026-10-27 night. For: the Vice Master (or the owner) at the editor. No Blueprint paste, only an asset import.

## Do

1. `git pull` the office repo.
2. In the Castle Defender editor, Output Log → Python:
   `py "<repo>/assets/checkking/Obsidian-Sovereign/Shoulders/import_shoulders_ue.py"`
   Creates `/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Shoulders/` with `SM_ObsidianSovereign_Shoulders_L`, `_R`, three 4K textures and `MI_ObsidianSovereign_Shoulders` (on the shared `M_ObsidianSovereign`).
3. **Don't re-import the chest.** The Vice Master already fitted and skinned it to `ShadowknightUE_SK` (#51, Tools/Obsidian_1027), and re-running `import_chest_ue.py` could overwrite that work. The chest FBX in the repo moved 0.97 m up into the set frame. That only matters for anyone starting from the raw FBX again.
4. Fitting the shoulders (and gauntlets) to the knight: same route as the chest (fit in Blender over ShadowknightUE_SK, transfer weights). The shoulders replace the knight's own pauldrons, which the chest work kept in `SK_Knight_ChestRemnant`.

## Check

- Drop chest + both shoulders into an empty level at 0,0,0: the pauldrons should sit on the chest's shoulder edges, with no gap or float (see `assets/checkking/Obsidian-Sovereign/Shoulders/renders/`).
- Not wired to the hero yet: fitting and skinning wait on the `ShadowknightUE_SK` FBX (issue #1).

Details: [assets/checkking/Obsidian-Sovereign/Shoulders/README.md](../../assets/checkking/Obsidian-Sovereign/Shoulders/README.md).
