#include "CDSwapScansCommandlet.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "CDActorCache.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphSchema_K2.h"
#include "Engine/Blueprint.h"
#include "FileHelpers.h"
#include "HAL/FileManager.h"
#include "K2Node_CallFunction.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/CompilerResultsLog.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"

DEFINE_LOG_CATEGORY_STATIC(LogCDSwap, Log, All);

namespace CDSwap
{
	struct FSwap { FName From; FName To; };

	const TArray<FSwap>& Swaps()
	{
		static const TArray<FSwap> List = {
			{ GET_FUNCTION_NAME_CHECKED(UGameplayStatics, GetActorOfClass),     GET_FUNCTION_NAME_CHECKED(UCDActorCacheLibrary, CachedGetActorOfClass) },
			{ GET_FUNCTION_NAME_CHECKED(UGameplayStatics, GetAllActorsOfClass), GET_FUNCTION_NAME_CHECKED(UCDActorCacheLibrary, CachedGetAllActorsOfClass) },
			{ GET_FUNCTION_NAME_CHECKED(UGameplayStatics, GetAllActorsWithTag), GET_FUNCTION_NAME_CHECKED(UCDActorCacheLibrary, CachedGetAllActorsWithTag) },
		};
		return List;
	}

	// The engine function this node really calls (resolved UFunction + owning class), or None if it is not one of ours to swap.
	FName SwapTarget(const UK2Node_CallFunction* Call)
	{
		const UFunction* Fn = Call ? Call->GetTargetFunction() : nullptr;
		if (!Fn || Fn->GetOwnerClass() != UGameplayStatics::StaticClass())
		{
			return NAME_None;
		}
		for (const FSwap& S : Swaps())
		{
			if (Fn->GetFName() == S.From) { return S.To; }
		}
		return NAME_None;
	}

	struct FSite
	{
		UK2Node_CallFunction* Node = nullptr;
		UEdGraph* Graph = nullptr;
		FName To;
	};

	TArray<FSite> FindSites(UBlueprint* BP)
	{
		TArray<FSite> Sites;
		TArray<UEdGraph*> Graphs;
		BP->GetAllGraphs(Graphs);   // ubergraph pages, functions, macros, collapsed / composite graphs
		for (UEdGraph* Graph : Graphs)
		{
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node);
				const FName To = SwapTarget(Call);
				if (!To.IsNone())
				{
					Sites.Add({ Call, Graph, To });
				}
			}
		}
		return Sites;
	}

	FString SiteText(const FSite& S)
	{
		return FString::Printf(TEXT("%s | graph %s | node %s | guid %s | %s"), *S.Node->GetBlueprint()->GetName(), *S.Graph->GetPathName(S.Node->GetBlueprint()),
			*S.Node->GetName(), *S.Node->NodeGuid.ToString(), *S.Node->GetTargetFunction()->GetName());
	}

	struct FCompileResult { bool bOk = false; int32 Errors = 0; int32 Warnings = 0; };

	FCompileResult Compile(UBlueprint* BP)
	{
		FCompilerResultsLog Results;
		Results.bSilentMode = true;
		FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::SkipSave | EBlueprintCompileOptions::SkipGarbageCollection, &Results);
		FCompileResult R;
		R.Errors = Results.NumErrors;
		R.Warnings = Results.NumWarnings;
		R.bOk = BP->Status != BS_Error && Results.NumErrors == 0;
		return R;
	}

	// Every (pin name, linked node, linked pin name) of a node, to check that the new node ends up with exactly the old connections.
	TSet<FString> LinkSet(const UEdGraphNode* Node)
	{
		TSet<FString> Out;
		for (const UEdGraphPin* Pin : Node->Pins)
		{
			for (const UEdGraphPin* L : Pin->LinkedTo)
			{
				Out.Add(FString::Printf(TEXT("%s|%d->%s.%s"), *Pin->PinName.ToString(), (int32)Pin->Direction, *L->GetOwningNode()->NodeGuid.ToString(), *L->PinName.ToString()));
			}
		}
		return Out;
	}

	// Replaces one node; false (with a reason) leaves the Blueprint in a state that must NOT be saved.
	bool SwapNode(UBlueprint* BP, const FSite& Site, FString& OutWhy)
	{
		UK2Node_CallFunction* Old = Site.Node;
		UEdGraph* Graph = Site.Graph;
		const UFunction* NewFn = UCDActorCacheLibrary::StaticClass()->FindFunctionByName(Site.To);
		if (!NewFn)
		{
			OutWhy = TEXT("library function not found");
			return false;
		}
		const TSet<FString> OldLinks = LinkSet(Old);
		const UEdGraphSchema* Schema = Graph->GetSchema();

		UK2Node_CallFunction* New = NewObject<UK2Node_CallFunction>(Graph);
		New->CreateNewGuid();
		New->SetFromFunction(NewFn);
		New->NodePosX = Old->NodePosX;
		New->NodePosY = Old->NodePosY;
		New->NodeComment = Old->NodeComment;
		New->bCommentBubbleVisible = Old->bCommentBubbleVisible;
		New->SetEnabledState(Old->GetDesiredEnabledState(), false);
		Graph->AddNode(New, false, false);
		New->AllocateDefaultPins();

		// Inputs first (defaults and links), so the output type follows the class pin (DeterminesOutputType), then outputs.
		for (int32 Pass = 0; Pass < 2; ++Pass)
		{
			const EEdGraphPinDirection Dir = Pass == 0 ? EGPD_Input : EGPD_Output;
			for (UEdGraphPin* OldPin : Old->Pins)
			{
				if (OldPin->Direction != Dir)
				{
					continue;
				}
				UEdGraphPin* NewPin = New->FindPin(OldPin->PinName, Dir);
				const bool bMatters = OldPin->LinkedTo.Num() > 0 || !OldPin->DoesDefaultValueMatchAutogenerated();
				if (!NewPin)
				{
					if (bMatters)
					{
						OutWhy = FString::Printf(TEXT("pin %s has no counterpart"), *OldPin->PinName.ToString());
						return false;
					}
					continue;
				}
				if (Dir == EGPD_Input)
				{
					NewPin->DefaultValue = OldPin->DefaultValue;
					NewPin->DefaultObject = OldPin->DefaultObject;
					NewPin->DefaultTextValue = OldPin->DefaultTextValue;
					New->PinDefaultValueChanged(NewPin);
				}
				if (OldPin->LinkedTo.Num() > 0)
				{
					const FPinConnectionResponse Moved = Schema->MovePinLinks(*OldPin, *NewPin, false, true);
					if (Moved.IsFatal())
					{
						OutWhy = FString::Printf(TEXT("links of pin %s could not move: %s"), *OldPin->PinName.ToString(), *Moved.Message.ToString());
						return false;
					}
					New->NotifyPinConnectionListChanged(NewPin);
				}
			}
			if (Pass == 0)
			{
				New->ReconstructNode();   // conform the output type to the class pin before outputs are linked
			}
		}

		// Every old link must now be on the new node, under the same pin names.
		const TSet<FString> NewLinks = LinkSet(New);
		for (const FString& L : OldLinks)
		{
			if (!NewLinks.Contains(L))
			{
				OutWhy = FString::Printf(TEXT("link lost: %s"), *L);
				return false;
			}
		}
		if (NewLinks.Num() != OldLinks.Num())
		{
			OutWhy = FString::Printf(TEXT("link count %d -> %d"), OldLinks.Num(), NewLinks.Num());
			return false;
		}
		Old->BreakAllNodeLinks();
		Graph->RemoveNode(Old);
		return true;
	}

	bool BackupFile(const UPackage* Package, const FString& Dir)
	{
		const FString File = FPackageName::LongPackageNameToFilename(Package->GetName(), FPackageName::GetAssetPackageExtension());
		const FString Dest = Dir / Package->GetName().RightChop(1) + FPackageName::GetAssetPackageExtension();
		return IFileManager::Get().Copy(*Dest, *File) == COPY_OK;
	}
}

int32 UCDSwapScansCommandlet::Main(const FString& Params)
{
	using namespace CDSwap;
	const bool bApply = FParse::Param(*Params, TEXT("apply"));
	const bool bDuplicate = FParse::Param(*Params, TEXT("duplicate"));
	FString AssetsArg, SkipArg, ReportPath;
	FParse::Value(*Params, TEXT("assets="), AssetsArg, false);
	FParse::Value(*Params, TEXT("skip="), SkipArg, false);
	if (!FParse::Value(*Params, TEXT("report="), ReportPath))
	{
		ReportPath = FPaths::ProjectSavedDir() / TEXT("CDSwapReport.txt");
	}
	TSet<FGuid> Skip;
	{
		TArray<FString> Parts;
		SkipArg.ParseIntoArray(Parts, TEXT(","));
		for (const FString& P : Parts) { FGuid G; if (FGuid::Parse(P.TrimStartAndEnd(), G)) { Skip.Add(G); } }
	}

	FAssetRegistryModule& Registry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
	Registry.Get().SearchAllAssets(true);
	TArray<FString> Paths;
	if (AssetsArg == TEXT("all"))
	{
		FARFilter Filter;
		Filter.PackagePaths.Add(TEXT("/Game"));
		Filter.bRecursivePaths = true;
		Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
		Filter.bRecursiveClasses = true;
		TArray<FAssetData> Assets;
		Registry.Get().GetAssets(Filter, Assets);
		for (const FAssetData& A : Assets) { Paths.Add(A.PackageName.ToString()); }
		if (bApply)
		{
			UE_LOG(LogCDSwap, Error, TEXT("-assets=all is inventory only; name the Blueprints to change"));
			return 1;
		}
	}
	else
	{
		AssetsArg.ParseIntoArray(Paths, TEXT(","));
	}

	TArray<FString> Report;
	const FString Stamp = FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S"));
	const FString BackupDir = FPaths::ProjectSavedDir() / TEXT("CDSwapBackup") / Stamp;
	int32 TotalCandidates = 0, TotalSwapped = 0, TotalSkipped = 0, TotalFailedBPs = 0, TotalRemaining = 0;
	Report.Add(FString::Printf(TEXT("CDSwapScans %s | apply %d | duplicate %d | %s"), *Stamp, bApply, bDuplicate, *Params));

	for (const FString& PathIn : Paths)
	{
		const FString Path = PathIn.TrimStartAndEnd();
		const FString ObjectPath = Path.Contains(TEXT(".")) ? Path : Path + TEXT(".") + FPackageName::GetShortName(Path);
		UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjectPath);
		if (!BP)
		{
			Report.Add(FString::Printf(TEXT("! %s: not a Blueprint / not found"), *Path));
			continue;
		}
		TArray<FSite> Sites = FindSites(BP);
		if (Sites.Num() == 0)
		{
			if (AssetsArg != TEXT("all")) { Report.Add(FString::Printf(TEXT("= %s: no engine world scans"), *BP->GetName())); }
			continue;
		}
		TotalCandidates += Sites.Num();
		Report.Add(FString::Printf(TEXT("# %s: %d call sites"), *BP->GetPathName(), Sites.Num()));
		for (const FSite& S : Sites) { Report.Add(TEXT("    ") + SiteText(S) + (Skip.Contains(S.Node->NodeGuid) ? TEXT("  [SKIP]") : TEXT(""))); }
		if (!bApply)
		{
			TotalRemaining += Sites.Num();
			continue;
		}

		if (bDuplicate)
		{
			IAssetTools& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get();
			UBlueprint* Copy = Cast<UBlueprint>(Tools.DuplicateAsset(BP->GetName() + TEXT("_SwapTest"), TEXT("/Game/_CDSwapTest"), BP));
			if (!Copy)
			{
				Report.Add(TEXT("  ! could not duplicate; nothing changed"));
				++TotalFailedBPs;
				continue;
			}
			BP = Copy;
			Sites = FindSites(BP);
		}

		// Baseline: this Blueprint and everything that depends on it (child Blueprints such as the rest of the HUD chain).
		TArray<UBlueprint*> Dependents;
		FBlueprintEditorUtils::GetDependentBlueprints(BP, Dependents);
		const FCompileResult Before = Compile(BP);
		TMap<UBlueprint*, FCompileResult> DepBefore;
		for (UBlueprint* D : Dependents) { DepBefore.Add(D, Compile(D)); }
		if (!Before.bOk)
		{
			Report.Add(FString::Printf(TEXT("  ! already has %d compile errors before any change: not touched"), Before.Errors));
			++TotalFailedBPs;
			TotalRemaining += Sites.Num();
			continue;
		}

		bool bFailed = false;
		int32 Swapped = 0, Skipped = 0;
		for (const FSite& S : Sites)
		{
			if (Skip.Contains(S.Node->NodeGuid))
			{
				++Skipped;
				continue;
			}
			FString Why;
			const FString Text = SiteText(S);
			if (!SwapNode(BP, S, Why))
			{
				Report.Add(FString::Printf(TEXT("  ! FAILED %s: %s"), *Text, *Why));
				bFailed = true;
				break;
			}
			++Swapped;
		}
		FCompileResult After;
		TArray<FString> DepProblems;
		if (!bFailed)
		{
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			After = Compile(BP);
			if (!After.bOk || After.Errors > Before.Errors)
			{
				bFailed = true;
				Report.Add(FString::Printf(TEXT("  ! compile after swap: %d errors (before %d)"), After.Errors, Before.Errors));
			}
			for (UBlueprint* D : Dependents)
			{
				const FCompileResult DA = Compile(D);
				if (DA.Errors > DepBefore[D].Errors || (!DA.bOk && DepBefore[D].bOk))
				{
					DepProblems.Add(FString::Printf(TEXT("%s %d->%d errors"), *D->GetName(), DepBefore[D].Errors, DA.Errors));
				}
			}
			if (DepProblems.Num() > 0)
			{
				bFailed = true;
				Report.Add(TEXT("  ! dependent Blueprints broke: ") + FString::Join(DepProblems, TEXT(", ")));
			}
		}
		const int32 Remaining = FindSites(BP).Num();
		if (bFailed)
		{
			++TotalFailedBPs;
			TotalRemaining += Sites.Num();
			Report.Add(TEXT("  NOT SAVED: the asset on disk is unchanged (this process ends without saving it)"));
			continue;
		}
		UPackage* Package = BP->GetOutermost();
		if (!bDuplicate && !BackupFile(Package, BackupDir))
		{
			++TotalFailedBPs;
			TotalRemaining += Sites.Num();
			Report.Add(TEXT("  ! backup copy failed: NOT SAVED"));
			continue;
		}
		const bool bSaved = UEditorLoadingAndSavingUtils::SavePackages({ Package }, false);
		TotalSwapped += Swapped;
		TotalSkipped += Skipped;
		TotalRemaining += Remaining;
		Report.Add(FString::Printf(TEXT("  OK swapped %d, skipped %d, remaining engine scans %d | compile errors %d->%d, warnings %d->%d | dependents checked %d | %s%s"),
			Swapped, Skipped, Remaining, Before.Errors, After.Errors, Before.Warnings, After.Warnings, Dependents.Num(),
			bSaved ? TEXT("saved") : TEXT("SAVE FAILED"), bDuplicate ? TEXT(" (copy)") : *(TEXT(", backup in ") + BackupDir)));
	}
	Report.Add(FString::Printf(TEXT("TOTAL candidates %d | swapped %d | skipped %d | Blueprints failed %d | engine scans remaining %d | %s"),
		TotalCandidates, TotalSwapped, TotalSkipped, TotalFailedBPs, TotalRemaining, bApply ? TEXT("applied") : TEXT("dry run, nothing changed")));
	FFileHelper::SaveStringArrayToFile(Report, *ReportPath);
	for (const FString& L : Report) { UE_LOG(LogCDSwap, Display, TEXT("%s"), *L); }
	return TotalFailedBPs > 0 ? 2 : 0;
}
