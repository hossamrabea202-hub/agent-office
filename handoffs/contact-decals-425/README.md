# #425 step 1: contact stains under wall-mounted props (i5 / adjustedfilm, 2026-11-02)

Research: [RESEARCH.md](RESEARCH.md). Rules applied (INDUSTRY_SECRETS section 0): 1 (locked-exposure judging), 3 (every
layer has a physical cause: soot rises, rust runs down, grime at the contact line), 6 (lookdev torch light 1800 K at the
flame), 10 (one material family for all props, so every wall agrees). Calibrated values from INDUSTRY_SECRETS 1.1.

## State
- **Built in CastleDefender6 (saved), all new, nothing live touched:** `/Game/CastleDefender/Environment/ContactDecals425/`
  - `M_ContactSootCard425`, `M_ContactMountCard425`: unlit Modulate stain cards (procedural HLSL, no textures, so no
    pbr_check input; the colours are the calibrated values above).
  - `MI_SootCard425_Torch`, `MI_MountCard425_Iron`, `MI_MountCard425_Wood`: tuned in lookdev (restraint pass).
  - `M_ContactSoot425`, `M_ContactMount425` + `MI_Soot425_Torch`, `MI_Mount425_Iron/_Wood`: DBuffer decal versions for
    walls that receive decals (not used by the placer now).
  - `M_LD_Grey18_425`: 0.18 grey for the lookdev bay.
- **Not placed in the level yet.** The swap-in waits for the owner's OK (office M: rule).

## Before / after (locked exposure, EV 1.5, no TAA)
- `cd425_22_before.png` / `cd425_22_after2.png`: WallTorch_Iron_04 in the castle (report index 22) (cards spawned, shot, removed again).
- `ld_tuned.png`: lookdev bay, 0.18 grey wall, 1800 K light at the flame (the mask shapes on a neutral wall).

## Place (after the owner's OK; the Master or i5)
```
py "<repo>/handoffs/contact-decals-425/place_contact425_ue.py"            # DRY RUN -> place_report.txt (79 props, 58 with a wall)
py "<repo>/handoffs/contact-decals-425/place_contact425_ue.py" --apply    # 58 mount cards + soot cards on torches with no TorchSoot card within 90 cm
py "<repo>/handoffs/contact-decals-425/place_contact425_ue.py" --remove   # undo: deletes every actor tagged CD425
```
Every card is tagged `CD425`, sits in the outliner folder `ContactDecals425`, has no collision and no shadow. Then save
the level on the Master. Backup = `--remove` (the cards are separate actors; no existing actor is changed).

## Checks
- [ ] Dry run lists 58 props with a wall; 21 skipped (free-standing trail torches, no wall within 70 cm).
- [ ] After `--apply`: soot rises from each wall torch's flame, grime ring + short rust runs under each iron bracket,
      faint grime under the signs and banner rods; no card floats or shows its square edge.
- [ ] Torches that already have a `TorchSoot_*` card get no second soot (check two of them).
- [ ] Play: nothing blocks the hero (no collision).

## Open / next
- Decision for the owner: turning **Receives Decals** back on for the castle walls would let DBuffer decals (and the
  existing moss / crack decals) show there; the cards don't need it.
- Old `TorchSoot_*` planes (48) could be replaced by the soot card for one consistent look (i9 found the pale-green strip
  issue near Vesna was the tower drum, not these).
- Step 2 of #425: wood, stone and grass/foliage realism passes; step 3: re-bake props that read fake.
