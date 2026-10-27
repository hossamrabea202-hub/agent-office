# Task #9 — Codex tower handoff

Owner reassigned this task to Codex. Status: requirements and reference acquisition, not a completed tower or permission to replace current castle actors.

Read [DESIGN_BRIEF.md](DESIGN_BRIEF.md). Footprint reference: four existing square tower footprints in a 2×2 block, then an approximately equal-area circular footprint. Soldiers must pass freely between adjoining walls through the tower at wall-walk height. Stairs and cannon space must not block that route.

## Requested read-only reference export

Master Agent: review `inspect_selected_tower_references.py`, select the existing tower/wall/walkway/stair/cannon actors in the current editor level, and run it with the UE Python menu. It writes only a new timestamped reference JSON under Saved/CodexTower09. It does not modify or save actors/assets. Syntax checked locally; not run in UE by Codex.

Put the JSON and overview/front/side screenshots into `handoffs/exports/codex/tower-9/`. Include measured wall heights/opening widths, desired tower height, actual soldier capsule/navigation settings, connection angles and cannon clearances. Do not upload licensed source meshes into the public repo.

Construction remains separate until these references exist. Candidate integration belongs in an isolated duplicate level, with a recoverable baseline and reviewed affected-actor list. The live castle is not a test scene.
