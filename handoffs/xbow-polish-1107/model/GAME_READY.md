# #561 crossbow: game-ready paste for i9 (checkking, 2026-11-07)

Owner, 2026-11-07: "make the xbow game ready asset then send it to i9, he will paste it to game." So the owner's OK is given.

**Asset:** `SM_Crossbow561`: 6,792 tris (LOD0), baked from a 1.7M-tri high poly; LOD1 50 %, LOD2 25 %; simple box
collision; one material `M_Crossbow561M`; 2K BaseColor (sRGB, Sharpen4), ORM (Masks, Composite Texture = normal), Normal
(BC5, green flipped: OpenGL bake); texture group Weapon; `pbr_check` OK. Lookdev shots: SCREENSHOTS, card #561.

**Zip:** `http://100.87.149.123:8765/files/124850_xbow561_model_v3.zip`. Unzip to e.g. `C:/Unreal Backups/_claude/xbow561m/`.

## Steps (editor Python, `git pull` first)
1. `py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --src "C:/Unreal Backups/_claude/xbow561m"`
   Dry run. Expect `files OK` and a `FIT scale ... rotation ... translation ...` line, plus the BP_Crossbow component that shows
   the old mesh and its override materials.
2. Same with `--import`: new assets in `/Game/CastleDefender/Equipment/crossbow/Rebuild561/`, **already fitted** to the
   old mesh's space (same bounds centre, length and axes; forward/up sign read from the `Muzzle` component), so the hand
   grip, the `Muzzle` and the `LoadedBolt` stay where they are. Last line: new bounds vs old bounds (should nearly match).
3. `--swap`: duplicates the old mesh to `Backup561/Noble_Crossbow_LowPoly_bak`, then Replace References
   (`consolidate_assets`) old → new: BP_Crossbow's component, its `SetStaticMesh` pins, Vesna's showcase, soldiers.
   Compile + save every BP the log lists.
4. If step 1 listed **override materials** on that component (the old atlas material), clear them on the component so
   `M_Crossbow561M` shows. Keep the #77 Overlay Material.

## Tests
1. Play, daylight: hero holds the new crossbow at the same grip (hands on the stock behind the trigger); brown walnut with
   grain, carved bone panels with brass nails, twisted string, worn steel bow.
2. Fire + reload: the bolt leaves from the same place as before; the loaded bolt lies on the stock top.
3. Swap to Golden Sovereign and back: both meshes show (only the Noble changed).
4. 20 m away: no sparkle; soldiers with crossbows look the same.

## If something is off (minor-fix rule: fix on the spot and note it on #561)
- Crossbow points backwards or upside down: on the crossbow mesh component add yaw 180 (or roll 180). Tell me which,
  I fix the fit for the next asset.
- Wrong size: the fit matches the old mesh's length; if the old one was much smaller/bigger, set component scale back.
- Undo everything: `--revert`.
Not run in UE by me (i5 has no editor driver on this card); the Python compiles and every call is the standard 5.x API.
