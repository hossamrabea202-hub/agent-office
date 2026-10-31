# #293 part 2: the blob mine as flesh (adjustedfilm, 2026-10-31)

The blob mine (`SM_Flora_BlobMine`) is pastel green with wood-grain lines, and it glows at `EmissiveBoost` 6.
`M_FleshSlime` replaces that look, following RESEARCH.md:
- dark, wet organic flesh (albedo 0.03–0.15), raised domain-warped veins, and green-grey rot patches;
- **wet 0.07–0.12 and tacky 0.42–0.48 roughness patches**;
- **life through subsurface** (deep red, stronger in the veins);
- **one faint danger cue:** the veins pulse at 0.35 Hz, barely visible except in the dark. No glow on the body.

It's procedural: no textures and no UVs, so it works on the existing mesh. Lookdev renders on the real mesh, 3 rounds:
`assets/adjustedfilm/FleshSlime293/renders/`.

## Steps (Master)

1. Run `py "<repo>/handoffs/blob-realism-293/setup_flesh293_ue.py" --dry-run`, then without `--dry-run`. It makes
   `M_FleshSlime` + `MI_BlobMine_Flesh` and **swaps nothing**.
2. Run `py ".../setup_flesh293_ue.py" --lookdev`. It places **FleshLookdev** (a copy of the mine with the new look) 2.5 m
   beside `Realm_BlobMine_04`.
3. **Take a before/after screenshot of the two side by side**, by day and at night, for the owner (`shot.js --card 293`).
4. **Only after the owner's OK:**
   - run `py ".../setup_flesh293_ue.py" --apply`, so every blob mine gets the flesh (BP_BlobMine's `Mine` component);
   - then run `--lookdev-remove`;
   - `--revert` puts `MI_Flora_BlobMine` back.

## Tuning (MI_BlobMine_Flesh)

| Parameter | Default | What it does |
|---|---|---|
| `Lump` | 3.5 cm | flesh lump size |
| `VeinCm` | 4 | vein scale |
| `Rot` | 0.7 | rot patches |
| `WetAmt` | 0.6 | wet areas |
| `Bump` | 1.2 | relief strength |
| `PulseHz` | 0.35 | how fast the veins pulse |
| `Danger` | 0.6 | how much the veins glow when they pulse; 0 = none |

The blob (`BP_JellyBlob`, `M_JellyBlob`) is part 3. Its Blueprint drives LandT, HatchT, ZShield, TScale, BornT and Green,
so it needs a reshade that keeps those parameters (M_JellyBlob's graph, not exported yet).
