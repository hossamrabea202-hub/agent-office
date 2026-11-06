# #333 Scorpion strike on packed soldiers (adjustedfilm, 2026-11-06)

Owner: "tanticle can attack soldier if 5 or more are packed together in formation and fighting within range (scorpion attack), blown up soldiers like when cannons shoot zombies."

## What it does (`wire_pack333_ue.py`, BPC_TentacleStrike)

- **Choosing:** at most every 1.5 s, a tentacle looks for a soldier in `StrikeRange` with at least `PackMin` (5) soldiers within 4 m, counting himself, and a zombie within 10 m. A zombie nearby stands in for "fighting". Otherwise the old cannon logic runs unchanged.
- **Counter-play:** a hidden marker is locked on the spot at the start. The strike plays its full 3.8 s wind-up, so soldiers who scatter are missed.
- **Hit:** soldiers within 4.5 m take `StrikeDamage` at the centre, falling to 35 % at the edge. Commanders take half. The dead ragdoll through their own death logic and get the cannon's impulse. Plus the cannon's camera shake, smoke, and the strike's own HitFX and HitSound.
- **Limits:** one pack strike per tentacle per 20 s. The hero is never targeted or hurt, and zombies are not hurt.

## Steps (Master, editor idle, not in Play)

1. `git pull`. Needs #532, applied.
2. `py handoffs/tentacle-style-530/wire_pack333_ue.py --dry-run`, then `--apply`. It does not save if it adds compile errors, and stops if a node name changed. Save all.
3. Play.

Revert: `wire_pack333_ue.py --revert`.

## Tests in Play

- Put 5+ soldiers in a fight within reach of a tentacle: the coil, the whip onto them, soldiers thrown like a cannon hit on zombies.
- 4 soldiers, or 5 with no zombie near: no pack strike.
- Move the soldiers away during the wind-up: it hits the empty spot.
- Commander survives a hit that kills a soldier next to him. The hero stays unhurt inside the blast.
- With many soldiers, no hitch from the search.

## Tested, and not tested

Lab, headless: dry-run, apply (84 nodes), refuses a second apply, revert, re-apply. Compile errors the same before and after (`CX_6`, `CX_7`, already failing in the lab).

**Not run in Play.** Unconfirmed: the blast feel, impulse on soldiers (it assumes their death ragdolls them immediately), damage values against soldier health, and the search cost, which is soldiers squared at worst per tentacle.
