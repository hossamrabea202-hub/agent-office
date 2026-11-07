// Swaps the engine's world-scan nodes for the cached ones (CDActorCache.h) inside chosen Blueprints, safely:
//   UGameplayStatics::GetActorOfClass      -> UCDActorCacheLibrary::CachedGetActorOfClass
//   UGameplayStatics::GetAllActorsOfClass  -> UCDActorCacheLibrary::CachedGetAllActorsOfClass
//   UGameplayStatics::GetAllActorsWithTag  -> UCDActorCacheLibrary::CachedGetAllActorsWithTag
// Replaces the round-2 Python scripts (hud_swap_scans_ue.py / reparent_hud_ue.py), fixing what the handoff listed:
//   - EVERY graph of the Blueprint (event graphs, functions, macros, collapsed graphs), not only the primary EventGraph
//   - nodes matched by the resolved UFunction and its owning class, never by display title
//   - every pin moved by name (exec, inputs, outputs, hidden world context), every default copied, every old link checked on the new node;
//     any missing pin or link aborts that Blueprint
//   - the Blueprint and every Blueprint depending on it are compiled before and after; the asset is saved only with no new compiler errors.
//     A commandlet edits memory only: a Blueprint that is not saved is left exactly as it was on disk (that IS the rollback)
//   - a byte copy of every saved .uasset goes to Saved/CDSwapBackup/<time>/ first
//   - report: candidates in all graphs, swapped, skipped, failed, remaining engine scans, with graph path and node GUID per call site
// Run (editor closed):
//   UnrealEditor-Cmd.exe <project> -run=CDSwapScans -assets=/Game/A/BP_X,/Game/B/BP_Y [-apply] [-duplicate] [-skip=<NodeGuid>,...] -unattended -nullrhi
//   no -apply: dry run, nothing changes.  -duplicate: work on copies in /Game/_CDSwapTest/ (originals untouched).
//   -assets=all: inventory every Blueprint under /Game (dry run only).
#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"
#include "CDSwapScansCommandlet.generated.h"

UCLASS()
class UCDSwapScansCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	virtual int32 Main(const FString& Params) override;
};
