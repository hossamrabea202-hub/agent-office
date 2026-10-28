Title: Cannons on the round towers: widen the traverse (aim arc)

Owner request (2026-10-28), Play screenshot from a mounted cannon on a round tower with a red arc drawn across the whole field in front:

> we can increase the range of movement of the cannons on the circle towers

**Today:** the mounted cannon yaw (A / D) is clamped to the same narrow arc everywhere, so on a round tower most of the field in view cannot be covered.

**Wanted**
- On the round towers the cannon can traverse the whole open arc of the parapet (about 150-180°, merlon to merlon), not just the straight-ahead cone.
- Yaw limits become a per-cannon setting (min / max yaw on BP_Cannon / the placed instance): default as today for the curtain-wall cannons, wide for the tower ones.
- The barrel never passes through a merlon: clamp so the muzzle clears the stone, or stop at the merlon edge. Soldiers manning it follow the rotation.
- Same for the aim helper / crosshair and the revenge-strike range check (tentacle code reads the cannon facing).

**Done when:** mounted on a round tower, A / D turn the cannon across the full field in front (the red arc), it never clips the parapet, and the wall cannons are unchanged.

---
Priority: normal
Pinned from the owner via hossam gmail (Claude), Master Agent. Agents: comment "Claimed by <your name>" to take it, close the issue when done.
