// Horde bake (owner, 2026-11-05). Writes the far-zombie crowd assets that UCDHordeSubsystem plays, following the contract in CDHordeAnimData.h:
//   /Game/CastleDefender/Horde/T_HordeZombie_Bones   bone texture (RGBA16F, 2 texels per bone, one row per frame)
//   /Game/CastleDefender/Horde/SM_HordeZombie        crowd mesh, LOD0 = skeletal LOD1, LOD1 = skeletal LOD3 (or reductions of LOD0), skin weights in UV1..UV4
//   /Game/CastleDefender/Horde/DA_HordeZombie        clip table + links (crowd materials: i5's script fills them; until then the zombie's own ones)
// Run:  UnrealEditor-Cmd.exe <uproject> -run=CDBakeHorde [-mesh=/Game/.../SK_Zombie] [-fps=30] [-dry]
// -dry samples and validates everything but saves nothing. Existing horde assets are updated in place (same object, same path).
#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"
#include "CDBakeHordeCommandlet.generated.h"

UCLASS()
class UCDBakeHordeCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	virtual int32 Main(const FString& Params) override;
};
