# #530 progress log (times UTC and approximate, 2026-11-06)

This log was written and pushed once, with the hand-off, not at each checkpoint.

- **10:20** Read the rules and the pipeline. Card #530 opened and claimed. The desk tick was refused: the seat `adjustedfilm (Claude)` is held by the idle session that started this task, and I did not use `--take-over`. No desk ticks from this session.
- **10:26** Lab exports of BPC_TentacleStrike and ABP_TentacleStrikePP. Timing from the class defaults: wobble 2.4, windup 1.3, strike 0.3, recover 2.0, so the hit is at 4.0 s. Target formulas read from the graph. No soldier targeting in this copy.
- **10:30** `gen_style.py`: Strike, Hunt A/B/C and Wounded authored. Seams 0.000 deg, numbers in README.md.
- **10:33** Preview bugs, all in the renderer, none in the clips:
  - An action needs its slot set to play on another armature (Blender 4.4+).
  - The clip keys the armature object's scale to 1, which shrank the mesh FBX hierarchy to 0.01.
  - `frame_set` does not restore channels whose keyed value did not change, so IK edits stuck on the frozen base bones. Now the renderer samples curves directly.
  - The UE clips hold empty curves that evaluate to 0, which collapsed the mesh. Now skipped.
- **10:35** Renders done. Today's arm goes in stiff, the new one lands in an arc. Stills checked by eye. The mp4s were rendered from the same code but not watched end to end.
- **10:37** Install, slot fix, wiring run in the lab. Found: 4 of 5 old clips differed by 1.9-2.3 deg from the authored clip, at seg_03 at worst. They appear to have no track on the frozen base bones, and `set_bone_track_keys` drops the write silently. Fixed with `add_bone_curve` first.
- **10:40** Full cycle in the lab passes: install, restore (0.00004 deg), reinstall, wire, refuse when wired, revert, rewire. Lab left installed and wired.
- **10:45** Hand-off. Waiting on: the i9 Master to apply, a fresh BPC_TentacleStrike export, the owner's play-test.
- **11:30 #533 spit + catapult.** Blob found to be 55 cm wide and spawned near the hero with no launch. Clips SPIT and CATAPULT authored, `import_spit_ue.py`, `wire_spit_ue.py` (207 nodes) pass the lab cycle. The editor offers no cast to the ABP from Python, so IK values are set by property name. A Play test in the lab is impossible, the component cannot compile there. Handed off untested in Play.
- **11:50 #533 trail and landing.** No Niagara can be authored by script and BP_BloodBurst is too heavy for a trail (24 physics chunks plus a decal), so: new light BP_BlobDrip_533 for flight, BP_BloodBurst + MI_BloodDecal_337 on landing. `wire_blobfx_ue.py` passes the lab cycle. Earlier spit and catapult previews drew blobs about 2.6x too big; re-rendered at true size. Not run in Play.
- **12:05 #333 pack strike.** `wire_pack333_ue.py` (84 nodes) passes the lab cycle. Handed off, not run in Play.
