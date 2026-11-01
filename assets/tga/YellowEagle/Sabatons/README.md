# Yellow Eagle Knight: Sabatons L + R (#367), v1 WIP

Made by TGA (Claude) on 2026-11-01 from Codex sheet 12 (`handoffs/knight-set-yellow/sheets/12_Sabatons.jpg`). Original and procedural.
- **Rebuild:** `tools/tga/knightset/build_sabatons.py`, then `tex_gauntlets.py` and `lookdev_gauntlets.py` with `PIECE=Sabatons`.
- **Same steel / brass / leather recipe** as the gauntlets and greaves.

**Status: first look for the owner. Not fitted and not imported yet.** `renders/sabatons_vs_sheet.jpg` shows the sheet above the model.

## What it is
- **Built to the sheet:** 28 cm long (11 cm toe + 17 cm mid and heel), 10.5 cm at the ball, 7 cm at the heel, 8.5 cm at the ankle, toe rising at about 22 degrees.
- **Steel:**
  - a pointed toe plate;
  - **5 shingled lames** and a vamp, whose edges lean back toward the heel down the sides (as the sheet);
  - side plates back to a heel cup;
  - an ankle cuff with a brass rolled rim.
- **Brass:** domed pivot rivets on both sides of each lame, rivets on the top line and round the cuff, and a strap buckle.
- **Leather:** a 5 mm sole with the sheet's outline, an ankle strap, and lining at the cuff's back.
- **Size:** 8.4k tris per foot. LOD1–3 come from the same script.
- **Textures:** 2K BC / ORM / N. pbr_check OK (metal 9 %, p50 179; non-metal p50 53). Mud sits on the sole edge and the toe.

## Frame and fit (next)
- **Canonical LEFT-foot frame:**
  - the bottom of the sole under the ankle is at the origin;
  - up is +Z;
  - the toe points toward −Y;
  - the outer side faces +X;
  - units are metres.
- The fit to `foot_l` / `foot_r` waits on #368.

## Known gaps vs the sheet
- The heel and side plates read boxy. The sheet's heel is a rounded cup with a seam, and its side plates curve into the cuff.
- The sheet's sole has a chevron tread and riveted edge; ours is plain leather.
- The warm bronze wash, the same open point as the rest of the set.
