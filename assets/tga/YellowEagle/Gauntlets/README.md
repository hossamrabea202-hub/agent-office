# Yellow Eagle Knight: Gauntlets L + R (#367), v1 WIP

Made by TGA (Claude) on 2026-10-31 from Codex sheet 08 (`handoffs/knight-set-yellow/sheets/08_Gauntlets.jpg`). Original and procedural. Rebuild it with `tools/tga/knightset`: `build_gauntlets.py`, then `tex_gauntlets.py`, then `lookdev_gauntlets.py`.

**Status: first look for the owner. Not fitted and not imported yet.** The renders in `renders/` include `gauntlets_vs_sheet.jpg`, the sheet next to the model.

## What it is
- **Built to the sheet's measurements:** 28 cm from cuff to fingertip, cuff 9.5 cm tall and 13.2 cm at its widest, hand 10.5 cm wide. The fingers sit in a relaxed curl.
- **Steel plates:**
  - a bell cuff with brass-bound rolled edges and 12 + 4 domed rivets;
  - 2 wrist lames and 2 metacarpal lames (each with rivets at both ends);
  - a knuckle lame with 4 bosses;
  - 3 lames per finger, with a dome over the fingertip;
  - 2 thumb lames.
- **Underneath:** a leather glove, plus a palm-side strap with a brass buckle.
- **Size:** 13.7k tris per hand at LOD0. LOD1, LOD2 and LOD3 are 6.9k, 3.4k and 1.6k.
- **Right hand:** an exact mirror of the left, sharing its UVs and textures.
- **Textures:** 2K `T_EagleGauntlets_BC` (sRGB), `_ORM` (AO / roughness / metallic, with metallic strictly 0 or 1), `_N` (DirectX).
  - `pbr_check` OK: non-metal p5/p50/p95 = 37/69/93 sRGB; metal is 42 % of the texels, p50 178 sRGB.
- **How the wear is placed:**
  - an AO mask puts oxide and grime (non-metal) in the seams and under the lames;
  - a bevel edge mask polishes the edges and the high points;
  - the plates have hammered pitting and fine scratches;
  - there is mud on the fingertips;
  - the leather has creases, and is darker in its recesses.

## Frame and fit (next)
- The meshes are in a **canonical left-hand frame**: the wrist joint is at the origin, the fingers point toward -Z, the back of the hand faces -Y, and the thumb points toward +X. Units are metres.
- **Placement waits on `handoffs/exports/master/knight_refpose.txt`** (read-only dump, `tools/tga/knightset/dump_knight_refpose_ue.py`). Once it lands, a fit script moves each hand onto `hand_l` / `hand_r` in the knight's ref pose. The setup then attaches each piece rigidly to its bone, the same way as the Obsidian set (`handoffs/obsidian-set-v2`). After that come the `pieces.csv` rows and the UE import script.

## Known gaps vs the sheet (v2 list)
- The steel still reads too bright and clean under studio light. The sheet's patina is darker, browner and etched, so the oxide coverage needs to go up.
- The palm leather is plain: it needs the sheet's stitched seams and padding.
- The fingers are smooth tubes under the lames: they need finger-joint gaps and more visible knuckle rows.
- Cuff rivets are only on the upper band; the sheet also has rows along the cuff edge.
