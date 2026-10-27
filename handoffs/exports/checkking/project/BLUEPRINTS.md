# Blueprint map (short)

- BP_ThirdPersonCharacter (Gameplay/ThirdPerson/Blueprints): hero; skills via BP_HeroAbilities, weapons BP_Crossbow, auras BP_HeroAuras.
- HUD chain (game HUD = BP_CommanderHUD): ZombieHUD <- Minimap <- SkillTree <- Barracks <- Army <- Controls <- Queue <- Hero <- Commander. Gold on BP_ZombieHUD.
- Soldiers: BP_SoldierSword / BP_SoldierXbow / BP_SoldierCommander (Characters/Knight), BP_SoldierLevelWatch, BP_SoldierLevelUpFX.
- Zombies: BP_Zombie, BP_ZombieWaveManager (spawner), BP_ZombieCharge, BP_JellyShieldAll, BP_ZombieJellyShield.
- Tentacles: BP_TentacleVitals + BPC_TentacleStrike + ABP_TentacleStrikePP; BP_ShockRider.
- Cannon: BP_Cannon + BPC_CannonBreak; BP_Cannonball (blast -> Ignite slime).
- Jelly/fire: BP_JellyBlob (mines), BP_JellyTrailManager.
- Level: /Game/ThirdPerson/Maps/ThirdPersonMap. Castle ~ x 0..4600, y 0..3450 (towers at corners, see ../codex/tower-9/MEASUREMENTS.md).
