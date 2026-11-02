# #433 P1: the kit shield is held edge-on, like a weapon (i5 / adjustedfilm, 2026-11-02)

**Cause:** BPC_ShieldKit places the shield (hero component `OffHand`, parented to bone `hand_l`) at per-shield
`GripLoc` / `GripRot`, and those were left at **0** when the kit was built (`setup_shieldkit_ue.py`: "tune later").
An identity rotation in the hand bone's frame lines the shield up with the hand like a blade.

**Fix (`fix_shield_grip_ue.py`, data only, no graph change):** per shield (Round, Heater, Gilded), compute the grip a
strapped shield has, from the hero's real skeleton (reference pose: `hand_l`, `lowerarm_l`) and the shield mesh bounds:
- the **face** (mesh's thinnest axis, boss side) points out of the back of the forearm;
- the **long axis** runs along the forearm;
- the **centre** sits on the forearm (35 % back from the wrist, 4 cm off the skin), not in the fist.
It writes `GripLoc` / `GripRot` on BPC_ShieldKit's defaults (small component; the hero BP is not touched).

## Run (after Alien's test; i5 or i9)
1. `py "<repo>/handoffs/shield-axis-433/fix_shield_grip_ue.py" --dry-run` → current (all 0) and computed values.
2. `py ".../fix_shield_grip_ue.py" --preview "<repo>/handoffs/shield-axis-433"` → a temporary hero mesh with each shield
   at the computed grip, front + side renders (`shield433_<i>_front/side.png`), actors deleted, nothing saved.
   Strap side facing out? Add `--flip` to both commands.
3. `py ".../fix_shield_grip_ue.py" --apply` → writes the defaults, compiles, saves BPC_ShieldKit
   (backup of the old values: `grip433_backup.json`). Undo: `--revert`.

## Checks (Play)
- [ ] Buy each shield: it sits flat on the left forearm, face out, long axis along the arm, in idle, run and block.
- [ ] The old built-in shield stays hidden while a kit shield is worn (#423).
- [ ] No clipping into the body in idle (if so: tune the 4 cm offset in the script, re-run --apply).

i5 run 15:56 (outside the session, nothing saved): dry run = all GripLoc/GripRot 0 (the cause); computed Round/Heater (r 91.2, p -66.1, y -80.0), Gilded (r -90.5, p -23.9, y 101.3). Preview renders `shield433_<i>_front/side.png` (reference pose): the shield lies along the forearm, on its outer side, hand at the grip. Apply in the live session (i9), then the Play check decides; `--flip` if the face is reversed.
