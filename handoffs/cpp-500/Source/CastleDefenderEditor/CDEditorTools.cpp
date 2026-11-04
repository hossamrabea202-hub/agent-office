#include "CDEditorTools.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EdGraph/EdGraph.h"
#include "Engine/Blueprint.h"
#include "K2Node_CallFunction.h"

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

	TArray<UEdGraph*> AllGraphs(UBlueprint* BP)
	{
		TArray<UEdGraph*> Graphs;
		BP->GetAllGraphs(Graphs);
		return Graphs;
	}
}

TArray<FString> UCDEditorTools::FindBlueprintsWithErrors(const FString& Path)
{
	TArray<FString> Lines;
	for (UBlueprint* BP : LoadBlueprints(Path))
	{
		bool bNodeError = false;
		for (UEdGraph* Graph : AllGraphs(BP))
		{
			for (const UEdGraphNode* Node : Graph->Nodes)
			{
				bNodeError |= Node && Node->bHasCompilerMessage && Node->ErrorType <= EMessageSeverity::Error;
			}
		}
		if (BP->Status == BS_Error || bNodeError)
		{
			Lines.Add(FString::Printf(TEXT("%s | status %d | node errors %s"), *BP->GetPathName(), (int32)BP->Status, bNodeError ? TEXT("yes") : TEXT("no")));
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
