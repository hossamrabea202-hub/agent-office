# #366 research: skin on long, animated, skinned meshes (adjustedfilm, 2026-10-31)

| Approach | Used by / source | Fit for the tentacles |
|---|---|---|
| Re-UV (straighten the shells, texel density matched) | Standard film/game practice; most correct | Needs the source mesh and a re-import. Not in the repo; the M: rule wants a new material only |
| World-aligned triplanar | Common for rocks / terrain (UE `WorldAlignedTexture`) | **Swims** on a skinned mesh that sways and curls (the texture stays in the world while the skin moves) |
| Triplanar or cylindrical mapping on the **pre-skinned** position | UE docs: *Pre-Skinned Local Position* "for effects that stick to a skeletal mesh"; used for creature skin detail | **Chosen.** The texture sticks to the skin through the sway and the #3 curl |
| Seam-free mips across the `atan2` wrap | Ben Golus, "Distinctive Derivative Differences" (2021): pick the smaller derivative of two wrapped UVs | Removes the one-pixel seam line along the tentacle |
| Normal maps under a new UV | Ben Golus, "Normal Mapping for a Triplanar Shader" (2017) | The mesh tangents follow the old UVs, so detail normals can rotate a little. Check in lookdev; if it shows, keep the normal sample on the old UV |

Texel density: the card asks for the castle stone's ~512 px/m. With 1024² skin textures, `SkinTileCm` = 200 gives
512 px/m. The script defaults to 100 cm (1024 px/m), because creature cells read smaller than stone. Tune it on the
material copy.
