# #277 variables (BPVar lines in VARIABLES_BPVar.txt)

| Blueprint | Name | Default | Meaning |
|---|---|---|---|
| BP_Flare | Target | 0,0,0 | set by BPC_Flares right after the spawn: the spotted threat |
| BP_Flare | Start | 0,0,0 | launch point |
| BP_Flare | T0 | 0.0 | game time of the launch |
| BP_Flare | Lit | false | ignited |
| BP_Flare | Life | 26.0 | seconds it burns |
| BP_Flare | FlareHeight | 2200.0 | cm over the target where it ignites |
| BP_Flare | FlareCd | 3500.0 | light candela at full burn |
| BP_Flare | Light | - | its light (tag FlareLight) |
| BPC_Flares | Owned | false | FLARES upgrade bought (saved, slot CastleSaveFlares) |
| BPC_Flares | Price | 400 | gold |
| BPC_Flares | NearShop | false | hero is at the barracks and can buy (prompt shown) |
| BPC_Flares | FWas | false | F held last check |
| BPC_Flares | DN | - | BP_DayNight |
| BPC_Flares | NextFlare | 0.0 | game time the next flare may go up |
| BPC_Flares | FlareGap | 6.0 | s between two flares |
| BPC_Flares | MaxFlares | 3 | flares burning at once |
| BPC_Flares | SightRange | 1400.0 | cm: closer threats are seen anyway (no flare) |
| BPC_Flares | SpotRange | 6000.0 | cm: how far a crossbowman spots |
| BPC_Flares | LitRadius | 2500.0 | cm: a burning flare this close already lights the spot |
| BPC_Flares | Shooter | - | the crossbowman picked this poll |
| BPC_Flares | BestScore | 0.0 | scratch |
| BPC_Flares | BestLoc | 0,0,0 | scratch |
| BPC_Flares | Found | false | scratch |
