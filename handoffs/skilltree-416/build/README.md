# #416 Weapon Mastery build (TGA): status and pick-up

**Not ready to paste yet.** The component is built and validated. The two hooks and the aura wiring wait on the live
5.8 exports requested on #416 (`handoffs/exports/master/2026-11-01/`: BP_SkillTreeHUD, BP_HeroAuras, BP_SkillUnlockFX
EventGraphs + `skilltree_live.png`).

## Done
| File | What |
|---|---|
| `BPC_SkillTome_graph.txt` | EventGraph of the new hero component (1,654 nodes, `applyall check` **Validation: OK**, casts PureState=Pure). Made by `tools/tga/vesna/gen_skill.py`. |
| `skill_data.json` | variables + table defaults (UVs into T_SK_Atlas, tab tables, prerequisite names) |
| `setup_tome_ue.py` | DRY_RUN by default: checks the assets, Level on the hero, and MPC_SkillTree St / RkA / RkB / Fx. Live: imports T_SK_Frame / T_SK_Atlas, creates BPC_SkillTome + its variables, and adds it to the hero as `SkillTome`. |
| `assets/tga/SkillTome/textures` | T_SK_Frame (1920×1080) and T_SK_Atlas (2048²), rendered by `tools/tga/vesna/render.ps1 -Only skill` |

What the component does is in `../DESIGN.md`:
- the five skills use the live rank rules and write exactly what the old up arrow wrote;
- E, the gold button or a double-click learns the next rank, with a shake and a message when it's refused;
- a 250 ms open fade, rows cascading in 40 ms apart, a pop on selection and on the learned diamond.

## Left (TGA, when the exports land)
1. Re-check the rank rules against the 5.8 graph. `gen_skill.py` carries the 10-30 numbers:
   - cost ×1 / ×5 / ×1 / ×5 / ×10;
   - the prerequisite chain;
   - the St / Fx writes.
2. **Auras** (`AURA_HOOK` in gen_skill.py): read the aura ranks from BP_HeroAuras, use its costs, and call its learn path. Then drop the "IN AURA PANEL" state.
3. **ArmoryHUD_TomeHook:** call `SkillTome.DrawTome(Self, SizeX, SizeY)` every frame, the same way as the MusterSeq.
4. **SkillTreeHUD_TomeGate:** while `SkillTome.Covering` is true, skip the old tree draw and its click handlers, and the aura panel's yellow boxes (CX_557 / 568 / 579). T / Esc open and close, pause and the unlock book stay as they are.
5. README paste steps, then the Play test from DESIGN §5, then the swap. The old graph stays as the backup; removing the gate restores it.
