// Read-only: writes every graph of the given Blueprints as text (node title, called function / variable, linked pins), plus component collision setup.
//   UnrealEditor-Cmd.exe <project> -run=CDDumpBlueprint -assets=/Game/A/BP_X,/Game/B/BP_Y -out=<file> -unattended -nullrhi
#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"
#include "CDDumpBlueprintCommandlet.generated.h"

UCLASS()
class UCDDumpBlueprintCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	virtual int32 Main(const FString& Params) override;
};
