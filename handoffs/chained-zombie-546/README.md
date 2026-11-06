# #546 Chained zombie in the back room

By `adjustedfilm (Claude)`, 2026-11-06. Owner's words are on the card. No paste: one script builds everything. New assets only; no live asset is edited.

## What the player gets

| Beat | What happens |
|---|---|
| Enter the room | He hangs on the east wall facing the door, wrists and ankles chained to 4 iron wall anchors, arms at 72 deg from hanging on average in the thrash loop (T-pose = 90, so **80 %**). He lunges, whips his head, hauls at one chain and then the other, and the chains stop him dead. Each yank clanks. Growls every 4-7 s, heard within 22 m. |
| First hit | The chain on the arm nearest the hero is cut: sparks, a thrown link, blood, a slash wound above the cuff. 4 links stay swinging on the wall, 2 dangle from the cuff. The arm drops, then he surges out at you. The other 3 chains still hold him. |
| Half free | Loose arm rakes and snatches. **Within 1.85 m it can hit the hero**: 14 damage, blow at 0.57 s, every 2.4-3.6 s. |
| Second hit | Locks up in a heat seizure, sags on what is left, and melts from the top down over 8.5 s. Arms wilt and draw back into the trunk, the top rounds over like a candle, a thin hot line runs down him with a real light riding it. Empty cuffs drop or swing on their chains as the heat reaches them. |
| After | A wet glowing pool cools over 30 s to marbled tallow. The chains and empty cuffs stay. His Tick then turns off. |

## Decisions

- **The room:** the small stone room behind the keep (inside x 3692-4108, y 1492-2008, 4.5 m high). East wall, centre y 1750, because it faces the door; the wall torch at (4101, 1733, z 325) lights him from above. The script re-traces wall, floor and anchors and stops if anything moved.
- **Not a BP_Zombie child.** BP_Zombie is counted by wave managers, soldiers and the C++ horde. He is a separate Pawn: waves, kill counts and soldier AI never see him. Soldiers do not attack him, he gives no XP (say if you want XP). Any damage counts as a slice, at most one per 0.5 s.
- **Not the live C++ candle melt.** `MF_CD_CandleMelt` is fed custom primitive data 8-15 from `AZombieBase` + the horde subsystem, and hides the mesh about 2.3 s after death. There is no entry point for a non-zombie actor, and 2.3 s is too short for a set piece. He gets a duplicate of `M_Zombie_Skin_AAA` with his own melt. So he keeps the live skin look; the tuning cvars `cd.Horde.*` do not affect him.
- **The claw can hurt:** yes, once half free only. It makes the second slice a risk, and stays fair because the wind-up is 0.36 s and the range is short. To turn it off, set `NextClaw` far ahead, or ask me.

## Steps (Master)

Editor idle, not in Play, main level open.

```
py "<repo>/handoffs/chained-zombie-546/chained_zombie_ue.py" --dry-run
py "<repo>/handoffs/chained-zombie-546/chained_zombie_ue.py"
```

The dry-run prints the wall and floor it found, and every optional sound or FX it could not find (those just stay silent). Then save the level. The first run compiles the new shaders once.

Rollback: `--revert` removes the placed actor (then save the level). The assets stay in `Characters/Enemies/Zombie/Chained546/` and nothing else references them; delete that folder by hand to remove them. To rebuild, delete `BP_ChainedZombie` by hand first (the script refuses to overwrite it).

**Check on the dry-run (i9 only):** it prints what feeds the WPO of the live `M_Zombie_Skin_AAA` there. The script replaces that WPO in the duplicate, but `MF_CD_CandleMelt` may also feed colour or emissive. See Play test 8.

## Play test

1. Walk into the room. He is on the east wall, feet on the floor, nothing floats, all 4 chains join wall to cuff.
2. Watch 30 s. Loop seam invisible, no pop. Chains go taut on the yanks, and sag when he slackens.
3. Cuffs sit round the forearm and shin, not inside them.
4. Slash him from his left: the LEFT arm comes free. Reload and slash from his right: the RIGHT arm does.
5. Half free, stand within about 1.5 m: he claws you, you lose 14 HP on the visible blow. Back off to 3 m: no damage.
6. One swing must never count twice: after the first hit he must still be alive.
7. Second hit: the 8.5 s melt plays, cuffs let go, the pool stays and cools. A third hit does nothing.
8. **The skin before the melt must look like any other zombie** with no glow or sag (see the dry-run check above). If it melts or glows early, tell i5: the live MF is reacting.
9. Light and exposure in the room: the glow must not blow out. `MeltGlow` (default 3.2) on `M_ChainedZombie_Melt`; `HeatLight` 28 cd in the BP.
10. Sounds: growl, chain clanks, sizzle. All come from existing cues; adjust volume on the nodes if too loud.
11. `stat unit` in the room: 24 links move every frame within 35 m.

## Tested and not tested

Full list: [TESTED.md](TESTED.md). In short: built, compiled and **run in Simulate in the lab** (`ckw/zlab`, an empty test room, real ticking animation and real ApplyDamage calls). **It has never run in Play, has never been on the real level, never been hit by the real sword, and the real sounds and particles have never played** (the lab has stubs for those).

## Files

| File | What |
|---|---|
| `chained_zombie_ue.py` | the install script (dry-run / apply / revert) |
| `gen_chain.py` | Blender source of the iron and the pool (procedural, original) |
| `fbx/` | 9 clips + 4 meshes |
| `preview/` | lookdev stills, lab captures from Unreal |

Rules applied: realism KB (calibrated PBR: iron 195 sRGB where rubbed bright, rust metallic 0 roughness ~1, oxide scale non-metal; wear by cause: rust where water sits, bright where link rubs link, rust runs down the wall under each anchor), lookdev with locked exposure and an 18 % grey ball. INDUSTRY_SECRETS rules 1, 2, 3, 5, 6 (1900 K light, slow drift + 9 Hz flutter), 8 (play rate varied, motion by pose-to-pose with overlap, no looped twin), 9 (wound by sphere mask on pre-skinned position), 10. No new textures, so `pbr_check.py` has nothing to run on; the iron values are in the material code.
