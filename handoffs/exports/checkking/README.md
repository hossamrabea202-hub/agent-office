# Exports for checkking (live editor, 2026-10-27)

From hossam gmail (Claude), Master Agent. Full Blueprint T3D exports (every graph), UTF-8. Build pastes on these and hand them back with `office.js handoff`; ask for a re-export if a graph changes. 5.3 paste rules: no `Ease` call nodes; GetArrayItem index pin is `Dimension 1`; IsValidIndex is `IndexToTest`; never write class names as `System.*`; calls to self custom events need the events compiled first; HUD children must hang off the real game HUD (BP_CommanderHUD now).

- `BP_Crossbow.t3d` (2267 KB): #19 crossbow camera lag. Graphs: EventGraph, ReceiveBeginPlay, ReceiveTick, UserConstructionScript, XbowHintEnd
- `BP_HeroHUD.t3d` (1134 KB): #24 auto death screen, level badge (game HUD chain: ...Queue <- Hero <- CommanderHUD). Graphs: EventGraph, ReceiveDrawHUD, UserConstructionScript
- `BP_JellyBlob.t3d` (269 KB): #18 blobs as mines. Graphs: EventGraph, ReceiveBeginPlay, ReceiveTick, UserConstructionScript
- `BP_JellyShieldAll.t3d` (178 KB): #18 jelly zombies. Graphs: EventGraph, ReceiveTick, UserConstructionScript
- `BP_SoldierLevelWatch.t3d` (119 KB): #2 soldier level-up FX. Graphs: EventGraph, ReceiveTick, UserConstructionScript
- `BP_ThirdPersonCharacter.t3d` (1190 KB): #24 hero damage/death, #7 sword slash, #19 crossbow aim camera. Graphs: CheckLevelUp, CustomEvent, EventGraph, OnBlendOut_A9FD76AC499F0F19AAFD89ADCAD2E10D, OnBlendOut_D2C7E3274B2FB7B79F44CBB7D36F5AFB, OnCompleted_A9FD76AC499F0F19AAFD89ADCAD2E10D, OnCompleted_D2C7E3274B2FB7B79F44CBB7D36F5AFB, OnInterrupted_A9FD76AC499F0F19AAFD89ADCAD2E10D, OnInterrupted_D2C7E3274B2FB7B79
- `BP_Zombie.t3d` (2418 KB): #24 zombie bite = damage causer, #18 hatch. Graphs: EventGraph, ReceiveAnyDamage, ReceiveBeginPlay, ReceiveTick, ResumeMove, Think, UserConstructionScript
- `BP_ZombieHUD.t3d` (18691 KB): #24 death screen ("YOU HAVE FALLEN" page), gold, HUD base. Graphs: EventGraph, ReceiveDrawHUD, UserConstructionScript
