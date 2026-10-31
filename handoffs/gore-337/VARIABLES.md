# #337 BPC_Gore337 variables

| Name | Default | Meaning |
|---|---|---|
| Hits | 0 | hits taken |
| Severed | - | bones already cut |
| MaxSevers | 2 | max limbs per zombie |
| HeavyFrac | 0.25 | heavy hit = this share of MaxHP or more |
| GoreLevel | 1 | 0 off (no splats, no severing), 1 reduced (default, no head), 2 full |
| LimbsOn | true | false = splats only |
| MeleeRange | 350.0 | cm: only hits from this close can sever |
| MaxLimbs | 8 | loose limbs in the world at once |
| BoneBase | ("ForeArm","Arm","Leg","Neck") | SK_Zombie bone per kind (with Left/Right) |
| ChildBase | ("Hand","ForeArm","Foot","Head") | the next bone down (sets the limb length) |
| Caps | - | set by the setup script: Forearm / UpperArm / Calf / Neck caps |
| DecalMat | - | set by the setup script: MI_BloodDecal_337 |
| Kind | -1 | state |
| CutBone | - | state |
| CutChild | - | state |
| ZMesh | - | state |
