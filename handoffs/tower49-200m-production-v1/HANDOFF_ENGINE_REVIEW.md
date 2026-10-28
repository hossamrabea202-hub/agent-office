# Tower #49 - authorized operator review

Owner-approved realistic medieval direction; 200 m above ground. The produced
static asset candidate is available as Tower49_Medieval_200m_v1.zip in the
owner's current Codex chat outputs. The ZIP has not been uploaded to a GitHub
release: the connected tools do not upload binary releases and this machine's
GitHub CLI has no login. Do not imply a public binary download exists.

The office handoff includes reproducible source scripts, measurements, mesh
audit and an actual-model preview. If the binary ZIP is not on the Unreal PC,
transfer it privately from the owner or reproduce with source/BUILD.md in a new
workspace. These are original tower sources; no licensed character source is
included. Do not run Blender authoring scripts in the Unreal Python console.

## Verified here

- 200 m highest battlement; 198 m roof; 1.798 m below-grade foundations.
- 1,296 treads, 9 turns, nominal 3 m stair width.
- LOD0: 239,676 instanced triangles, 20 unique mesh datablocks in the assembly.
- LOD1/LOD2 counts are in reports/final-audit.json; three materials.
- No degenerate faces or non-manifold edges in the final geometry audit.
- UV0 and UV1 present. Baked tangent normal maps and packed ORM supplied.
- 3,888 floor probes and 3,888 vertical 2 m headroom probes passed.
- Independent FBX reimport preserved units/bounds/topology.
- All three GLBs passed the explicit static policy; canonical package hash check
  passed. Consult reports and SHA256SUMS.txt for the actual file identities.

These are not Unreal Play, capsule sweeps, AI navigation, GPU performance or
final AAA art acceptance. The candidate needs human review at gameplay distance
and close camera. Do not close #49 based on these static results alone.

## Operator checks

1. Import into a NEW review folder/isolated test level. Preserve the current
   castle, existing actors, maps, materials and dependencies. Do not integrate
   automatically. Verify centimeters/meters, orientation and the ground datum.
2. Build stone/wood/iron materials from the map guide. Inspect tangent normals
   and NormalDX green convention under the real game lighting. Confirm UV0 tile
   density, UV1 padding at chosen lightmap resolution and absence of material
   seams/aliasing. Use the matched modular FBXs and their UCX hulls.
3. Test the real hero capsule: ground start, all base-transition sections, long
   climb, turns and roof exit. The roof has an open outer stairwell sector at
   315..360 degrees and an inner edge guard; approach corbels are removed to keep
   headroom. Test 2 m clearance with actual capsule and camera, not only rays.
4. Check collision: no hull across the hollow interior/route, no rail bypass or
   collision snag, roof/floor support, entrance opening/header and arrow slits.
   Some wall collision strips are intentionally coarse and need engine review.
5. Inspect LOD transitions at actual screen sizes, draw calls and memory. Prefer
   HISM/instance reuse and vertical streaming chunks; choose Nanite/LOD settings
   from measured baseline/candidate results. Do not assume a static poly count
   proves the target frame rate.
6. Report screenshots and pass/fail in the cafeteria. Owner reviews the isolated
   asset before live-castle integration. Gameplay systems on #49 (wind, grab,
   fog, tentacles, blobs, zombies, inscriptions, checkpoints and summit reward)
   remain a separate integration phase.

Keep the sources and provenance intact. This is a review handoff, not permission
to replace or save over the current castle.

