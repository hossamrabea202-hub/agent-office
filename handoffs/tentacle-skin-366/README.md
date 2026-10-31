# #366 tentacle skin stretched along the tentacles

By `adjustedfilm (Claude)`, 2026-10-31 night. Card #366 (owner: "what about the stretch in tanticles skin").
Known facts, from #3 / `REWORK_BONE_CURL.md`: there is one mesh, `SK_CorruptedTentacle_01` (14-bone chain, about
254 m long at placed scale), with the material `M_CorruptedTentacle_Ripple2`. No export of the material graph exists,
so the script reads it in the editor.

## What the fix does

The script makes a **copy** of the tentacle material, `M_…_UV366`, and copies any material instances, re-parented to it.
Every colour, crack and roughness texture in the copy reads a length-aware UV:
- **Along the tentacle:** world centimetres, with the actor's scale included, divided by `SkinTileCm`.
- **Around the tentacle:** the angle, times a whole number of tiles, so the texels come out square at the mean girth.

The UV is built from the **pre-skinned** position, so the skin does not slide while the tentacle sways or curls. The
seam where the angle wraps uses seam-free mips. Textures that drive the ripple's World Position Offset are left alone.
The red glowing cracks and the wet green skin keep their own colours, because only the UVs change.
The live material is **never** edited. The swap uses a backup and has `--revert`.

## Steps (Master: paste only)

1. `py "<repo>/handoffs/tentacle-skin-366/fix_tentacle_uv366_ue.py" --info`. This is read-only. Push
   `tentacle366_info.txt`. It lists the tentacle actors, their slots and materials, the mesh's long axis and every
   texture sample.
2. `py ".../fix_tentacle_uv366_ue.py" --build --dry-run`, then `--build`. This only makes new `*_UV366` assets.
3. **Before/after:**
   1. Screenshot one big tentacle, for example `TentacleHit_T_5`, from the wall.
   2. Run `--apply TentacleHit_T_5`. Take the same shot.
   3. Post both with `tools/shot.js --card 366`.
4. Wait for the owner's OK.
   - **OK:** run `--apply Tentacle --dry-run`, then `--apply Tentacle`. This swaps all tentacles.
   - **No:** run `--revert`. It puts back every slot it swapped.

## Checks

1. The cells and cracks look the same size along and around the tentacle, with no long streaks.
2. During the sway, the skin moves with the tentacle and doesn't slide over it.
3. No hard seam line runs along the tentacle.
4. The red cracks still glow, and the ripple rings still run.
5. If the cells look too big or small, change `SkinTileCm` on `M_…_UV366`. 200 matches the castle stone's 512 px/m.
6. If the bumps look wrongly lit, tell me on #366. I'll keep the normal map on the old UVs; that is one line.

Not run in the editor yet. Step 1 (`--info`) is read-only and shows whether the 5.3 graph walk finds the samples.

Rules applied: M: (research first, new material only, before/after, swap on OK with dry-run and revert);
INDUSTRY_SECRETS rule 1 (judge it in lookdev at locked exposure), §1 (texel density matched to the castle).
