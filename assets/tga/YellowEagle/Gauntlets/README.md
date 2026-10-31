# Yellow Eagle Knight: Gauntlets L + R (#367), v2

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
- **Size:** 15.7k tris per hand at LOD0 (v2). LOD1, LOD2 and LOD3 are 7.9k, 3.9k and 1.9k.
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

## v2 (2026-11-01, night plan)
`renders/gauntlets_vs_sheet.jpg` shows v2 under the sheet.
- **Steel is now blackened.** A fine fire-scale film (non-metal, blue-black, satin) covers most of each plate. Bright metal shows only where it's worn: edges, high spots and fine flakes. Rust-gold speckle sits in the pits.
  - pbr_check OK: metal 11 % of texels, p50 179 sRGB; non-metal p50 54.
  - **Bake fix:** on bare-metal / film borders, the bake's anti-aliasing mixed in the dark film colour, while the 0 / 1 metallic threshold still classed those texels as metal. They're now lifted to the knowledge base's metal floor (luminance 150 sRGB).
  - **Gotcha:** for byte images, Blender's `Image.pixels` are sRGB-encoded, not linear.
- **Fingers:** 20 % longer and straighter (the sheet's ~11 cm), with **4 lames each** (the proximal one is split in two).
- **Cuff:** a close **row of 24 small rivets under the brass rim**.
- **Palm:** the leather has a light tooled swirl.
- **Size:** 15.7k tris per hand. LODs 7.9k / 3.9k / 1.9k.
- The stale `_ROD` FBXs from v1's naming bug are deleted.

## Known gaps vs the sheet (next)
- The sheet's whole plate has a warm bronze wash; ours is neutral steel. That's a tint on the film, for after the owner's look.
- The sheet's palm has a riveted border and a deeper tooled pattern. Its cuff is a little shorter relative to the hand.
- Fit on the knight still waits on `knight_refpose.txt` (#368).

