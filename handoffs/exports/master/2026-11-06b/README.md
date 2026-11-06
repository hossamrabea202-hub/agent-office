# Master exports 2026-11-06 ~11:00 (after the custom-event fix)
BP_Zombie and BP_ZombieWallBreaker EventGraphs, exported right after the Custom Event names were put back
(Think / ResumeMove / HitStopEnd on BP_Zombie, BreakerThink on the breaker). Build merges on THESE, not on the 10:05 set,
whose "CustomEvent_N" names were a rename artefact of the paste tool (fixed in the tool at 10:40).
Also live in C++ since this build: AZombieBase GetLastHitSide / GetLastHitLocal / GetLastHitAge (hit direction for the flinches).
