# Prompt for the next adjustedfilm session on the i5 laptop (paste it as the first message)

```
You are adjustedfilm (Claude), the agent seat on the i5 laptop in the agent-office repo
(C:\Users\hossam.rabea\agent-office). Read handoffs/laptop-i5/NEXT_SESSION_PROMPT.md and follow it.
```

Start: `git pull` (stash `handoffs/motion-graphics-66`, `handoffs/obsidian-set-v2`, `tools/applyall/__pycache__` first),
read AGENTS.md (rules `W:` / `AR` / `M:`), `handoffs/laptop-i5/README.md` (the pick-up tables at the bottom), tick with
`--start --take-over`, read the inbox, start the watcher (`node tools/watch.js --seat "adjustedfilm (Claude)" --every 5`).

**Do, in order, without asking:**

1. **#322 part 2, Flesh Brute animation polish.** The export is in `handoffs/exports/adjustedfilm/brute-322/`
   (BP_FleshBrute_EventGraph.txt + FB_assets_and_placed.txt, 37 FB_ anims):
   - play-rate variety and a heavy gait matched to the move speed;
   - blends between anims instead of snaps;
   - HP ×4 on spawn.

   Pre-check, then hand off.
2. **#297 part 3, mine dungeon.** Place TGA's #309 MineKit (`assets/tga/MineKit`, layout in its README) as an
   always-loaded sub-level far under the map, put one BP_CaveDoor at Mine_01's mouth and one in the dungeon (Targets
   paired), and swap the door mesh to TGA's SM_Mine_Door. Do it all as one placement script with `--dry-run`.
3. **#278 flares:** ask the Master for the BPC_Flares compile warning text, then fix it.
4. **#293 part 3, jelly blobs:** request the M_JellyBlob graph export. The new look must keep LandT, HatchT, ZShield,
   TScale, BornT and Green.
5. **Answer as data lands:**
   - #296 (setup_caverock296.txt / screenshot; owner PRIORITY);
   - #316 (breach_dump.json: check the Rubble* / Brk* names);
   - #269 (diag_reveal268.txt);
   - #183 (screenshot + BP name).
6. **Keep TGA busy:** TGA has #332 (whiteboard cleanup) and #49 (the 250 m spiral tower, owner-assigned). Next for TGA:
   #187 gold coin pile, #186 forge.

**Tools:**
- bpkit generators: `tools/laptop2/bpgen/bpkit.py`. Set `HERE` again after `from bpkit import *`.
- Pre-checks: `tools/applyall/fix_impure.py`, `applyall check`, and `merge --dry-run`. One cast per consumer.
- Use `K2_GetComponentsByClass`; no self-calls to own events (use timers by name).
- Python: Blender's, with `-I`. Put helper scripts in `~/ckw`, because of the 260-character path limit.
