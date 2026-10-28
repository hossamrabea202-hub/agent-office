Title: Bug: after E (mount) the hero stands in front of the cannon; place him behind or beside it

Owner report (2026-10-28), Play screenshot from the mounted-cannon view on a round tower: the hero is standing in front of the barrel, between the wheels, in the line of fire and in the middle of the cannon view.

> the hero can't stand like this in the scene when we click E to mount: place the main character in the correct position (right behind or beside the cannon)

**Wanted**
- On E (mount) the hero moves to a fixed gunner spot on the cannon: a socket or scene component on BP_Cannon (behind the breech, or at the side by the wheel, facing the muzzle direction), attached so he turns with the cannon when aiming.
- Gunner pose / idle (hands on the cannon), reacts to the recoil.
- Never in front of the muzzle and never in the camera's way; if the gunner spot is blocked (soldier, wall), use the other side.
- On E (dismount) he steps back to a free spot behind the cannon, not onto the parapet or through the wheel.
- Same placement for soldiers ordered to man a cannon (crew spots by the wheels, never in front).

**Done when:** in Play, mounting any cannon puts the hero behind or beside it, he stays there while aiming and firing, nothing stands in front of the muzzle, and dismounting leaves him on walkable ground.

---
Priority: high
Pinned from the owner via hossam gmail (Claude), Master Agent. Agents: comment "Claimed by <your name>" to take it, close the issue when done.
