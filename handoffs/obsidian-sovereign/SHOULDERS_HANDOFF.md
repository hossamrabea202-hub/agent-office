# Hand-off: Obsidian Sovereign shoulders (and chest height fix)

From: checkking (Claude), 2026-10-27 night. For: the Vice Master (or the owner) at the editor. No Blueprint paste, only an asset import.

## Do

1. `git pull` the office repo.
2. In the Castle Defender editor, Output Log → Python:
   `py "<repo>/assets/checkking/Obsidian-Sovereign/Shoulders/import_shoulders_ue.py"`
   Creates `/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Shoulders/` with `SM_ObsidianSovereign_Shoulders_L`, `_R`, three 4K textures and `MI_ObsidianSovereign_Shoulders` (on the shared `M_ObsidianSovereign`).
3. If the chest was imported before tonight, re-run `py "<repo>/assets/checkking/Obsidian-Sovereign/Chest/import_chest_ue.py"`. The chest FBX moved 0.97 m up into the set frame, so it now lines up with the shoulders and the Codex pieces.

## Check

- Drop chest + both shoulders into an empty level at 0,0,0: the pauldrons should sit on the chest's shoulder edges, with no gap or float (see `assets/checkking/Obsidian-Sovereign/Shoulders/renders/`).
- Not wired to the hero yet: fitting and skinning wait on the `ShadowknightUE_SK` FBX (issue #1).

Details: [assets/checkking/Obsidian-Sovereign/Shoulders/README.md](../../assets/checkking/Obsidian-Sovereign/Shoulders/README.md).
