# Hand-off: Obsidian Sovereign gauntlets

From: checkking (Claude), 2026-10-28. For: the Vice Master (or the owner) at the editor. Asset import only, no Blueprint paste.

1. `git pull` the office repo.
2. In the editor, Output Log → Python: `py "<repo>/assets/checkking/Obsidian-Sovereign/Gauntlets/import_gauntlets_ue.py"`
   Creates `/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Gauntlets/` with `SM_ObsidianSovereign_Gauntlets_L`, `_R`, three 4K textures and `MI_ObsidianSovereign_Gauntlets`.
3. Check: drop chest, shoulders and both gauntlets at 0,0,0. The hands sit where the Codex hands were (below the forearms).

Not wired to the hero yet: fitting and skinning wait on the `ShadowknightUE_SK` FBX (issue #1).
Details: [assets/checkking/Obsidian-Sovereign/Gauntlets/README.md](../../assets/checkking/Obsidian-Sovereign/Gauntlets/README.md).
