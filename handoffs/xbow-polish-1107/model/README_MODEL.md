# #561 pass 3 (current): high poly baked to low poly (checkking, 2026-11-07)

Owner: "more detailed, a couple million polys, then bake it on a low poly ... same quality with minimum tris."
**Use this version (v2 zip), not the pass-2 v1 zip.** Script: `build_xbow561_hp.py` (`--stage high`, then `--stage bake`).
- HIGH: 1,718,716 tris. Real geometry for the carved staghorn scrolls (0.45 mm deep), domed brass rivets, hammer marks on
  the steel, growth-ring relief on the walnut, 3-strand twisted string, 2-strand twisted bridle cords, a 2.5 mm bolt groove.
- LOW (the game mesh): **6,792 tris**, one slot, 2K BaseColor / ORM / Normal baked from the HIGH (selected-to-active,
  extrusion 3 mm, ray 9 mm). Inlay, rivets, pins and groove exist only in the bake. `pbr_check` OK (non-metal p50 79 sRGB,
  metal p50 190, metallic 0/1).
- Zip for the Master: `http://100.87.149.123:8765/files/124424_xbow561_model_v2.zip` (same file names, same steps below).
  The HIGH .blend (92 MB) stays on i5: `C:/Users/hossam.rabea/ckw/xbow561/hp/xbow561_high.blend`.
- Known: spiral lines step a little at extreme close-up (2K texel limit; fine at play distance); steel oxide patches
  could be finer; bake has a small dark smudge where the crossed bridle meets the stock top.

---

## (pass 2, replaced) Noble crossbow rebuilt as a real object

Owner: "I want it to show in game as if it is a real world object ... do it, and even tweak the design if necessary."
This **replaces** pass 1 (the texture recalibration in `../README.md`): the old mesh is too simple for close-up realism.
Our own model (no licensed parts), built by script: `build_xbow561.py`. Study: `../RESEARCH.md`.

## What it is
Late-15th-century German steel-prod hunting crossbow, 88 cm long, 68 cm span, 30,024 tris, one material slot,
2K texture set (BaseColor, ORM, Normal), origin at the nut, X forward, Z up, cm.
- oiled walnut stock with real grain (~80 sRGB), finish rubbed lighter on edges, hand polish on the grip, dirt in recesses
- engraved staghorn inlay on both sides of the butt, brass rivets along it
- forged steel prod (bow), spanned, tapering to the tips, bare worn steel with dark oxide in hollows and patches
- string = 3 twisted waxed-hemp strands (modelled, not a texture), loops round the tips
- cord bridle lashing the prod to the stock, antler nut with fingers and steel side plates, long iron trigger, iron stirrup
- design tweaks vs the old one: real proportions (dropped butt, slim fore-end), steel prod instead of a flat bar, bridle, stirrup

Checks done on i5: `pbr_check` **OK** (non-metal p50 80 sRGB, metal p50 190, metallic 0/1, roughness 0.30-0.75).
Lookdev (locked exposure, grey 18 % + chrome ball): office SCREENSHOTS, card #561.
Rules applied: KB 1 (calibrated values), 2 (lookdev with locked exposure), 3 (wear by physics: edges by ray bevel, cavities
by AO, grip polish, no global grunge), 4 (detail sized to texel density, imported normals); INDUSTRY_SECRETS rules 1-3,
§1.3.1 Composite Texture, §1.3.6 Sharpen4, §1.3.8 Masks/BC5; owner decal rule (new assets only).

## Master: steps
1. Download `http://100.87.149.123:8765/files/124424_xbow561_model_v2.zip`, unzip to e.g.
   `C:/Unreal Backups/_claude/xbow561m/`.
2. `git pull`. Output Log (Python): `py "<repo>/handoffs/xbow-polish-1107/model/import_xbow561_ue.py" --src "C:/Unreal Backups/_claude/xbow561m"`
   → `dry run: files OK`.
3. Same with `--import` → `imported + saved: /Game/CastleDefender/Equipment/crossbow/Rebuild561`. New assets only:
   `SM_Crossbow561`, `M_Crossbow561M`, 3 textures. Nothing live changes.
4. Screenshot it in the editor (drop it in the lookdev map / viewport, daylight) for the owner. **Owner OK first.**
5. After the OK: `... --fit` prints the scale and offset that put the new mesh where the old one sits. In `BP_Crossbow`,
   on the component that shows `Noble_Crossbow_LowPoly`: Static Mesh = `SM_Crossbow561`, apply the printed scale/offset
   (backup the BP first). Same on `BP_TradeShowcase` / soldier crossbows if they show the Noble mesh. Compile, save.
   If the hero's hands sit wrong on the grip, note the transform on #561 and I adjust (minor-fix rule).

## Tests
1. `M_Crossbow561M` compiles, no errors; the mesh shows wood, bone, steel, brass, hemp (not grey or black).
2. Play, daylight, hero aiming: walnut grain visible, string twist visible up close, steel edges catch the sun, no sparkle at 20 m.
3. Fire + reload still work (the mesh swap changes nothing in the graph); the LoadedBolt still sits on the stock top
   (the new stock has a bolt groove forward of the nut; the bolt may need a small Z offset).
4. LV4 electric overlay (#77): set Overlay Material on the new mesh component too.

## Known limits (next round)
Inlay scroll pattern is procedural and a bit regular; the steel oxide patches could be finer; the nut is plain. Golden
Sovereign and the bolt (SM_XbowBolt) are not rebuilt yet.
