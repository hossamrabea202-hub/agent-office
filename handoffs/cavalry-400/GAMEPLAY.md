# #404 Heavy cavalry: gameplay design (checkking, 2026-11-01)

Research: `RESEARCH.md` §5 (couched lance, closed line, full speed **at** impact, ride through, wheel, re-form; a
charge that stops in a crowd loses everything).

## Numbers

| | |
|---|---|
| Price | 400 gold (a soldier is cheaper: a knight with a barded destrier is the elite unit) |
| Limit | 4 knights (one "lance" in the medieval sense) |
| Where | at the **stables** if an actor with the tag `Stables` is in the level (the #401 building), otherwise at the barracks NPC; key **L** |
| HP | 600 (horse + rider as one unit) |
| Charge | accelerates 450 → 950 cm/s over 2 s, straight at the target |
| Lance hit | 140 × speed factor (0.35 – 1.2) to the first zombie in front within 2.8 m, launch 900 forward + 350 up |
| Trample | 35 to every other zombie in the front cone within 2.5 m at impact, then 18 once per zombie while riding through |
| Lance breaks | 30 % per hit; without a lance the hit is 70 (horse + sword); a fresh lance at the rally point |
| Ride through | 14 m past the impact, no stopping |
| Wheel | back to the rally point at 650 cm/s, then 3 s rest before the next charge |
| Rally point | 8 m behind the hero, knights spaced 3 m side by side (slot 0..3) |
| Acquire | the nearest zombie within 35 m |
| Bogged | slower than 250 cm/s with 4+ zombies within 3 m: 30 HP/s lost ("pulled down by the mob") |

## Behaviour (Think, every 0.2 s)

1. Count zombies near the knight; find the nearest live one within 35 m (dying zombies, life span > 0, are skipped).
2. **Bogged** check (above).
3. By state:
   - **0 Follow:** ride to the rally point (gallop if far, walk if near). If a zombie is in range and the rest time is
     over: lock the charge line and go to 1.
   - **1 Charge:** speed ramps up; steer at the target, aiming past it so the horse never brakes. Impact when a zombie
     is within 2.8 m in front (cone 60°): lance hit, trample cone, lance may break → 2. Gives up after 6 s → 3.
   - **2 Ride through:** keep going 14 m along the charge line, trampling once per zombie → 3 after 3.5 s or at the end.
   - **3 Wheel:** back to the rally point; there (or after 7 s): re-arm the lance, rest 3 s → 0.
4. **Animation:** speed picks Idle / Walk / Trot / Gallop and the play rate follows the speed within 0.8 – 1.2
   (INDUSTRY_SECRETS 3.4: never more than ±20 %). The lance is upright in Idle / Walk / Trot and couched in the
   Gallop, because it is skinned to the clips' `lance` bone.

Death: the horse falls (A_Destrier_Death), collision off, the lance is hidden, a notice "A knight has fallen.", gone
after 12 s.

## Decisions

- **BP_Cavalry is a plain Character, not a child of BP_SoldierSword** (same reason as the medics #185): the soldier's
  Tick brain would order, form and slash with it. The rider's body is the soldier's own mesh, copied by the setup
  script, so the look matches the army and no licensed file is duplicated.
- **Zombies don't target the cavalry in v1.** Its danger is being bogged in a crowd, which is exactly the historical
  weakness, and it keeps the zombie AI untouched. A zombie-target hook can come later.
- **No HUD line in v1:** the recruit notice shows the count (n/4). A BPC_MotionFX line needs a fresh export and a
  merge; it can follow the medics' pattern later.
- **No player control of the charge in v1:** the knights pick targets near the hero. An orders-wheel "charge there"
  command (#12) is a natural v2.
