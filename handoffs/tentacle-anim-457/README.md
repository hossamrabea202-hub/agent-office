# #457 Polish the tentacle animations (i5, 2026-11-03)

Owner order (Alien, via TGA, chat 979). Before/after: `out/ab_A.mp4` (12 s, left old / right new), `out/grid_A.png`.

## What was wrong (analyze.py on the live clips)
- SK_CorruptedTentacle_01 has a 14-bone chain. In every Ripple / Sway clip the **base 4 bones never move** (0 deg range),
  so the arm hinges at seg_04 like a pipe.
- The rest is **one 20 s sine of 3-6 deg per bone**: no secondary motion, no tip action, no curl. It is smooth and
  seamless, just mechanical.
- The 8 placed tentacles were already de-synced (their own clip, rate and start), so the fix belongs in the clips.

## New clips (gen_anim.py, octopus-arm reference: bends travel base -> tip, the tip is most active, slow reach/curl)
Layered, all 14 bones, 40 s seamless loop (whole cycles only; loop seam 0 deg), amplitude envelope base 0.15x -> tip 1x:
primary elliptical sway (2 / 40 s), travelling wave climbing the arm (5-7 / 40 s, 0.55 rad lag per bone), tip flick
(13-17 / 40 s, last 40 %), 2 eased curl events per loop (outer half rolls in and out), slow twist.
Seeds: A (1, amp 1.0), B (2, amp 1.15), C (3, amp 0.9). Mapping: Ripple -> A, Sway000/020 -> B, Sway030/040 -> C.

## In Unreal (new assets only)
- `tentacle_anim_ue.py import`: AS_Tentacle_Polish457_A/B/C in `/Game/CastleDefender/Environment/Tentacles/Rig/Polish457`
  (done and saved on i5).
- Round trip checked (`pose_check_ue.py`): bone translations are identical to the old clips (0.000 cm), and rotations
  differ by 9-16 deg at most, which is the animation itself, not an axis flip.
- **Swap only after Alien's OK:** `swap --dry-run`, then `swap --apply`. This covers all 8 Env_CorruptedTentacle actors and
  their JellyShell; each keeps its rate and start. Revert: `swap --revert` (backup `tentacle_anim_backup.json`).
- Not touched: the strike (BPC_TentacleStrike + ABP_TentacleStrikePP). That is the next pass if Alien wants the attacks polished too.
