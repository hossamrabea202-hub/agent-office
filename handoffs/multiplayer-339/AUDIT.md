# #339 slice 1: single-player audit (from the exports in handoffs/exports, newest per Blueprint)

By `adjustedfilm (Claude)`, 2026-10-31. Made by a read-only scan of the T3D exports. Every **player-0 call** must become "the hero / controller of this castle's team" (slice 2). Economy vars move per team. Save/load becomes per match. Blueprints with no export yet are not in the list; the editor-side audit (every BP) comes with slice 2.

| Blueprint | player-0 calls | save/load | economy vars | HUD calls | export |
|---|---|---|---|---|---|
| BP_Crossbow | 27 | 0 | - | 5 | `handoffs/exports/master/2026-10-30b/BP_Crossbow_EventGraph.txt` |
| BP_FleshBrute | 13 | 0 | XP | 1 | `handoffs/exports/adjustedfilm/brute-322/BP_FleshBrute_EventGraph.txt` |
| BP_Zombie | 12 | 0 | XP | 0 | `handoffs/exports/master/2026-10-30b/BP_Zombie_EventGraph.txt` |
| BP_BarracksHUD | 10 | 0 | Gold | 6 | `handoffs/exports/master/2026-10-30b/BP_BarracksHUD_EventGraph.txt` |
| BP_HeroHUD | 6 | 0 | - | 3 | `handoffs/exports/master/2026-10-30b/BP_HeroHUD_EventGraph.txt` |
| BP_HalfHorseZombie | 6 | 0 | XP | 0 | `handoffs/exports/master/2026-10-30b/BP_HalfHorseZombie_EventGraph.txt` |
| BP_TentacleVitals | 5 | 0 | Gold | 3 | `handoffs/exports/master/2026-10-31/BP_TentacleVitals_EventGraph.txt` |
| BP_ThirdPersonCharacter | 4 | 0 | XP | 0 | `handoffs/exports/master/2026-10-30b/BP_ThirdPersonCharacter_EventGraph.txt` |
| BP_SkillTreeHUD | 4 | 0 | Gold | 3 | `handoffs/exports/master/2026-10-30b/BP_SkillTreeHUD_EventGraph.txt` |
| BP_NoticeHUD | 4 | 0 | - | 3 | `handoffs/exports/master/2026-10-30b/BP_NoticeHUD_EventGraph.txt` |
| BP_SoldierSword | 3 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_SoldierSword_EventGraph.txt` |
| BP_QueueHUD | 3 | 2 | Gold, XP | 3 | `handoffs/exports/master/2026-10-30b/BP_QueueHUD_EventGraph.txt` |
| BP_BlobMine | 3 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_BlobMine_EventGraph.txt` |
| BP_ZombieWaveManager | 2 | 0 | - | 2 | `handoffs/exports/master/2026-10-30b/BP_ZombieWaveManager_EventGraph.txt` |
| BP_ZombieHUD | 2 | 0 | Gold, XP | 2 | `handoffs/exports/master/2026-10-30b/BP_ZombieHUD_EventGraph.txt` |
| BP_Whirlwind | 2 | 0 | - | 0 | `handoffs/exports/checkking/skills/BP_Whirlwind.t3d` |
| BP_QuakeSlam | 2 | 0 | - | 0 | `handoffs/exports/checkking/skills/BP_QuakeSlam.t3d` |
| BP_MinimapHUD | 2 | 0 | - | 3 | `handoffs/exports/master/2026-10-30b/BP_MinimapHUD_EventGraph.txt` |
| BP_HeroAbilities | 2 | 0 | - | 0 | `handoffs/exports/checkking/skills/BP_HeroAbilities.t3d` |
| BP_Fissure | 2 | 0 | - | 0 | `handoffs/exports/checkking/skills/BP_Fissure.t3d` |
| BP_CommanderHUD | 2 | 0 | Gold | 3 | `handoffs/exports/master/2026-10-30b/BP_CommanderHUD_EventGraph.txt` |
| BP_CastleGateControl | 2 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_CastleGateControl_EventGraph.txt` |
| BP_ArmoryHUD | 2 | 2 | Gold | 3 | `handoffs/exports/master/2026-10-30b/BP_ArmoryHUD_EventGraph.txt` |
| BP_ZombieJellyShield | 1 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_ZombieJellyShield_EventGraph.txt` |
| BP_ZombieCharge | 1 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_ZombieCharge_EventGraph.txt` |
| BP_WallBreachSpot | 1 | 0 | - | 1 | `handoffs/exports/master/2026-10-31/BP_WallBreachSpot_EventGraph.txt` |
| BP_SoldierCommander | 1 | 0 | - | 1 | `handoffs/exports/master/2026-10-30b/BP_SoldierCommander_EventGraph.txt` |
| BP_SkillBookPickup | 1 | 0 | - | 0 | `handoffs/exports/laptop2/prompt68/BP_SkillBookPickup.t3d` |
| BP_RisenDirector | 1 | 0 | - | 1 | `handoffs/exports/master/2026-10-30b/BP_RisenDirector_EventGraph.txt` |
| BP_MapPickup | 1 | 0 | - | 0 | `handoffs/exports/laptop2/prompt68/BP_MapPickup.t3d` |
| BP_JellyBlob | 1 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_JellyBlob_EventGraph.txt` |
| BP_CrossbowBolt | 1 | 0 | XP | 0 | `handoffs/exports/master/2026-10-30b/BP_CrossbowBolt_EventGraph.txt` |
| BP_ControlsHUD | 1 | 0 | - | 3 | `handoffs/exports/master/2026-10-30b/BP_ControlsHUD_EventGraph.txt` |
| BP_CastleGateLever | 1 | 0 | - | 0 | `handoffs/exports/master/2026-10-30b/BP_CastleGateLever_EventGraph.txt` |
| BP_Cannonball | 1 | 0 | Gold | 2 | `handoffs/exports/master/2026-10-31/BP_Cannonball_EventGraph.txt` |
| BP_BagPickup | 1 | 0 | - | 0 | `handoffs/exports/laptop2/prompt68/BP_BagPickup.t3d` |
| BP_ArmyHUD | 1 | 0 | - | 3 | `handoffs/exports/master/2026-10-30b/BP_ArmyHUD_EventGraph.txt` |

Total player-0 calls: 134 in 37 Blueprints
