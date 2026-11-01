# #404 variables (BPVar lines in VARIABLES_BPVar.txt)

| Blueprint | Name | Default | Meaning |
|---|---|---|---|
| BP_Cavalry | State | 0 | 0 follow, 1 charge, 2 ride through, 3 wheel, 9 dead |
| BP_Cavalry | Slot | 0 | place in the line (0..3) |
| BP_Cavalry | HP | 600.0 | hit points (horse + rider) |
| BP_Cavalry | MaxHP | 600.0 |  |
| BP_Cavalry | Anim | -1 | clip playing: 0 idle, 1 walk, 2 trot, 3 gallop |
| BP_Cavalry | Target | - | charge target (BP_Zombie) |
| BP_Cavalry | BestZ | - | scratch: nearest live zombie |
| BP_Cavalry | Best | 0.0 | scratch: its distance |
| BP_Cavalry | NearCount | 0 | zombies within 3 m |
| BP_Cavalry | Zs | - | zombies this think (BP_Zombie array) |
| BP_Cavalry | Hit | - | already hit this charge |
| BP_Cavalry | ChargeDir | - | locked charge line |
| BP_Cavalry | RideEnd | - | end of the ride-through |
| BP_Cavalry | StateT | 0.0 | time the state began |
| BP_Cavalry | NextCharge | 0.0 | rest until |
| BP_Cavalry | LanceBroken | false |  |
| BP_Cavalry | Bogged | false | slow in a crowd: losing HP |
| BP_Cavalry | RiderDrop | -92.0 | cm: rider pelvis into the saddle (tune by eye) |
| BP_Cavalry | Acquire | 3500.0 | cm: charge range |
| BP_Cavalry | ChargeSpeed | 950.0 | cm/s at full gallop |
| BP_Cavalry | LanceDmg | 140.0 |  |
| BP_Cavalry | TrampleDmg | 35.0 |  |
| BP_Cavalry | BogDPS | 30.0 |  |
| BPC_Cavalry | Count | 0 | knights alive (counted every second) |
| BPC_Cavalry | MaxKnights | 4 | limit |
| BPC_Cavalry | Price | 400 | gold per knight |
| BPC_Cavalry | NearShop | false | hero at the stables / barracks (offer shown) |
| BPC_Cavalry | LWas | false | L held last check |
| BPC_Cavalry | Shop | - | the stables (tag Stables) or the barracks NPC |
| BPC_Cavalry | ZHud | - | BP_ZombieHUD (gold) |
