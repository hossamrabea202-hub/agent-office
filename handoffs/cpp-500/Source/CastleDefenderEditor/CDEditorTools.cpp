#include "CDEditorTools.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "Engine/Blueprint.h"
#include "K2Node_CallFunction.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Logging/TokenizedMessage.h"
#include "Modules/ModuleManager.h"

namespace
{
	TArray<UBlueprint*> LoadBlueprints(const FString& Path)
	{
		FAssetRegistryModule& Registry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		FARFilter Filter;
		Filter.PackagePaths.Add(FName(*Path));
		Filter.bRecursivePaths = true;
		Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
		Filter.bRecursiveClasses = true;
		TArray<FAssetData> Assets;
		Registry.Get().GetAssets(Filter, Assets);
		TArray<UBlueprint*> Out;
		for (const FAssetData& Asset : Assets)
		{
			if (UBlueprint* BP = Cast<UBlueprint>(Asset.GetAsset()))
			{
				Out.Add(BP);
			}
		}
		return Out;
	}

	TArray<UEdGraph*> AllGraphs(const UBlueprint* BP)
	{
		TArray<UEdGraph*> Graphs;
		BP->GetAllGraphs(Graphs);
		return Graphs;
	}
}

TArray<FString> UCDEditorTools::FindBlueprintsWithErrors(const FString& Path, bool bRecompile)
{
	TArray<FString> Lines;
	for (UBlueprint* BP : LoadBlueprints(Path))
	{
		if (bRecompile)
		{
			FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::SkipSave);
		}
		int32 NodeErrors = 0;
		for (const UEdGraph* Graph : AllGraphs(BP))
		{
			for (const UEdGraphNode* Node : Graph->Nodes)
			{
				if (Node && Node->bHasCompilerMessage && Node->ErrorType <= EMessageSeverity::Error)
				{
					++NodeErrors;
				}
			}
		}
		if (BP->Status == BS_Error || NodeErrors > 0)
		{
			Lines.Add(FString::Printf(TEXT("%s | status %d | nodes with errors %d"), *BP->GetPathName(), (int32)BP->Status, NodeErrors));
		}
	}
	for (const FString& L : Lines) { UE_LOG(LogTemp, Warning, TEXT("CD errors: %s"), *L); }
	return Lines;
}

TArray<FString> UCDEditorTools::FindExpensiveCalls(const FString& Path)
{
	static const TSet<FName> Expensive = {
		TEXT("GetAllActorsOfClass"), TEXT("GetAllActorsWithTag"), TEXT("GetAllActorsOfClassWithTag"), TEXT("GetActorOfClass"),
		TEXT("GetAllActorsWithInterface"), TEXT("GetAllWidgetsOfClass"), TEXT("LineOfSightTo"), TEXT("GetComponentsByClass"),
		TEXT("LineTraceSingle"), TEXT("LineTraceMulti"), TEXT("SphereOverlapActors"), TEXT("FindNearestActor") };
	TArray<FString> Lines;
	for (UBlueprint* BP : LoadBlueprints(Path))
	{
		for (UEdGraph* Graph : AllGraphs(BP))
		{
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				const UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node);
				if (Call && Expensive.Contains(Call->FunctionReference.GetMemberName()))
				{
					Lines.Add(FString::Printf(TEXT("%s | %s | %s | %s"), *BP->GetName(), *Graph->GetName(), *Node->GetName(), *Call->FunctionReference.GetMemberName().ToString()));
				}
			}
		}
	}
	for (const FString& L : Lines) { UE_LOG(LogTemp, Display, TEXT("CD expensive: %s"), *L); }
	return Lines;
}
