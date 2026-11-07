#include "CDEditorTools.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "Engine/Blueprint.h"
#include "K2Node_CallFunction.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Self.h"
#include "K2Node_Event.h"
#include "K2Node_CustomEvent.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "Components/SceneComponent.h"
#include "ScopedTransaction.h"
#include "Editor.h"
#include "K2Node_DynamicCast.h"
#include "EdGraphSchema_K2.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Logging/TokenizedMessage.h"
#include "Modules/ModuleManager.h"
#include "EdGraphUtilities.h"
#include "Misc/FileHelper.h"

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

FString UCDEditorTools::SetNodePinDefault(const FString& BlueprintPath, const FString& NodeName, const FString& PinName, const FString& NewValue, bool bCompile)
{
	const FString ObjPath = BlueprintPath.Contains(TEXT(".")) ? BlueprintPath : BlueprintPath + TEXT(".") + FPackageName::GetShortName(BlueprintPath);
	UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjPath);
	if (!BP) { return FString::Printf(TEXT("ERROR no Blueprint %s"), *ObjPath); }
	for (UEdGraph* Graph : AllGraphs(BP))
	{
		if (!Graph) { continue; }
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node || Node->GetName() != NodeName) { continue; }
			UEdGraphPin* Pin = Node->FindPin(FName(*PinName), EGPD_Input);
			if (!Pin) { return FString::Printf(TEXT("ERROR %s has no input pin %s"), *NodeName, *PinName); }
			if (Pin->LinkedTo.Num() > 0) { return FString::Printf(TEXT("ERROR %s.%s is wired, no literal"), *NodeName, *PinName); }
			const FString Old = Pin->GetDefaultAsString();
			const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
			Node->Modify();
			Schema->TrySetDefaultValue(*Pin, NewValue);
			const FString Now = Pin->GetDefaultAsString();
			FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
			if (bCompile) { FKismetEditorUtilities::CompileBlueprint(BP); }
			const FString Res = FString::Printf(TEXT("OK %s %s.%s: %s -> %s%s"), *BP->GetName(), *NodeName, *PinName, *Old, *Now,
				BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
			UE_LOG(LogTemp, Display, TEXT("CD pin: %s"), *Res);
			return Res;
		}
	}
	return FString::Printf(TEXT("ERROR node %s not found in %s"), *NodeName, *BP->GetName());
}

namespace
{
	// "Node" = first node with that name in any graph; "Graph:Node" (e.g. "EventGraph:CX_3") = only in that graph
	// (node names are unique per graph, not per Blueprint: construction scripts reuse names).
	UEdGraphNode* FindNodeByName(UBlueprint* BP, const FString& InName, UEdGraph** OutGraph = nullptr)
	{
		FString GraphName, Name = InName;
		InName.Split(TEXT(":"), &GraphName, &Name);
		if (GraphName.IsEmpty()) { Name = InName; }
		for (UEdGraph* Graph : AllGraphs(BP))
		{
			if (!Graph) { continue; }
			if (!GraphName.IsEmpty() && Graph->GetName() != GraphName) { continue; }
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (Node && Node->GetName() == Name) { if (OutGraph) { *OutGraph = Graph; } return Node; }
			}
		}
		return nullptr;
	}
}

FString UCDEditorTools::InsertPinFilter(const FString& BlueprintPath, const FString& TargetNode, const FString& TargetPin, const FString& FunctionPath,
	const FString& ExtraArgPin, const FString& ExtraSource)
{
	const FString ObjPath = BlueprintPath.Contains(TEXT(".")) ? BlueprintPath : BlueprintPath + TEXT(".") + FPackageName::GetShortName(BlueprintPath);
	UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjPath);
	if (!BP) { return FString::Printf(TEXT("ERROR no Blueprint %s"), *ObjPath); }
	FString ClassPath, FuncName;
	if (!FunctionPath.Split(TEXT(":"), &ClassPath, &FuncName)) { return TEXT("ERROR FunctionPath needs Class:Function"); }
	UClass* FuncClass = LoadObject<UClass>(nullptr, *ClassPath);
	UFunction* Func = FuncClass ? FuncClass->FindFunctionByName(FName(*FuncName)) : nullptr;
	if (!Func) { return FString::Printf(TEXT("ERROR no function %s"), *FunctionPath); }

	UEdGraph* Graph = nullptr;
	UEdGraphNode* Target = FindNodeByName(BP, TargetNode, &Graph);
	if (!Target) { return FString::Printf(TEXT("ERROR node %s not found"), *TargetNode); }
	UEdGraphPin* TPin = Target->FindPin(FName(*TargetPin), EGPD_Input);
	if (!TPin) { return FString::Printf(TEXT("ERROR %s has no input %s"), *TargetNode, *TargetPin); }
	UEdGraphPin* OldSource = TPin->LinkedTo.Num() > 0 ? TPin->LinkedTo[0] : nullptr;
	if (OldSource)
	{
		if (const UK2Node_CallFunction* Prev = Cast<UK2Node_CallFunction>(OldSource->GetOwningNode()))
		{
			if (Prev->GetTargetFunction() == Func) { return FString::Printf(TEXT("SKIP %s.%s already filtered by %s"), *TargetNode, *TargetPin, *FuncName); }
		}
	}

	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
	Graph->Modify();
	Target->Modify();
	UK2Node_CallFunction* Call = NewObject<UK2Node_CallFunction>(Graph);
	Call->CreateNewGuid();
	Call->SetFromFunction(Func);
	Call->NodePosX = Target->NodePosX - 320;
	Call->NodePosY = Target->NodePosY + 160;
	Graph->AddNode(Call, false, false);
	Call->PostPlacedNewNode();
	Call->AllocateDefaultPins();

	// first data input of the function, skipping self / world context
	UEdGraphPin* FirstIn = nullptr;
	for (UEdGraphPin* P : Call->Pins)
	{
		if (P->Direction == EGPD_Input && P->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec && !P->bHidden && P->PinName != UEdGraphSchema_K2::PN_Self
			&& P->PinName.ToString() != ExtraArgPin) { FirstIn = P; break; }
	}
	UEdGraphPin* Ret = Call->GetReturnValuePin();
	if (!FirstIn || !Ret) { Graph->RemoveNode(Call); return TEXT("ERROR function needs an input and a return value"); }

	FString Log;
	if (OldSource)
	{
		TPin->BreakLinkTo(OldSource);
		if (!Schema->TryCreateConnection(OldSource, FirstIn)) { Log += TEXT(" [old->in FAILED]"); }
	}
	else
	{
		Schema->TrySetDefaultValue(*FirstIn, TPin->GetDefaultAsString());
	}
	if (!Schema->TryCreateConnection(Ret, TPin)) { Log += TEXT(" [ret->target FAILED]"); }

	if (!ExtraArgPin.IsEmpty() && !ExtraSource.IsEmpty())
	{
		FString SrcNode, SrcPin;
		ExtraSource.Split(TEXT("."), &SrcNode, &SrcPin);
		UEdGraphNode* S = FindNodeByName(BP, SrcNode);
		UEdGraphPin* SP = S ? S->FindPin(FName(*SrcPin), EGPD_Output) : nullptr;
		UEdGraphPin* AP = Call->FindPin(FName(*ExtraArgPin), EGPD_Input);
		if (!SP || !AP || !Schema->TryCreateConnection(SP, AP)) { Log += FString::Printf(TEXT(" [extra %s FAILED]"), *ExtraSource); }
	}
	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	const FString Res = FString::Printf(TEXT("%s %s: %s.%s <- %s(%s)%s%s"), Log.IsEmpty() ? TEXT("OK") : TEXT("PARTIAL"), *BP->GetName(), *TargetNode, *TargetPin,
		*FuncName, OldSource ? *FString::Printf(TEXT("%s.%s"), *OldSource->GetOwningNode()->GetName(), *OldSource->PinName.ToString()) : TEXT("literal"), *Log,
		BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
	UE_LOG(LogTemp, Display, TEXT("CD filter: %s"), *Res);
	return Res;
}

FString UCDEditorTools::ConnectPins(const FString& BlueprintPath, const FString& FromNodeDotPin, const FString& ToNodeDotPin)
{
	const FString ObjPath = BlueprintPath.Contains(TEXT(".")) ? BlueprintPath : BlueprintPath + TEXT(".") + FPackageName::GetShortName(BlueprintPath);
	UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	FString FN, FP, TN, TP;
	FromNodeDotPin.Split(TEXT("."), &FN, &FP);
	ToNodeDotPin.Split(TEXT("."), &TN, &TP);
	UEdGraphNode* A = FindNodeByName(BP, FN);
	UEdGraphNode* B = FindNodeByName(BP, TN);
	UEdGraphPin* PA = A ? A->FindPin(FName(*FP), EGPD_Output) : nullptr;
	UEdGraphPin* PB = B ? B->FindPin(FName(*TP), EGPD_Input) : nullptr;
	if (!PA || !PB) { return FString::Printf(TEXT("ERROR pin not found %s -> %s"), *FromNodeDotPin, *ToNodeDotPin); }
	A->Modify(); B->Modify();
	const bool bOK = GetDefault<UEdGraphSchema_K2>()->TryCreateConnection(PA, PB);
	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	return FString::Printf(TEXT("%s %s -> %s%s"), bOK ? TEXT("OK") : TEXT("ERROR connect refused"), *FromNodeDotPin, *ToNodeDotPin, BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
}

FString UCDEditorTools::GetPinSource(const FString& BlueprintPath, const FString& NodeName, const FString& PinName)
{
	const FString ObjPath = BlueprintPath.Contains(TEXT(".")) ? BlueprintPath : BlueprintPath + TEXT(".") + FPackageName::GetShortName(BlueprintPath);
	UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjPath);
	UEdGraphNode* N = BP ? FindNodeByName(BP, NodeName) : nullptr;
	UEdGraphPin* P = N ? N->FindPin(FName(*PinName), EGPD_Input) : nullptr;
	return (P && P->LinkedTo.Num() > 0) ? P->LinkedTo[0]->GetOwningNode()->GetName() : FString();
}

FString UCDEditorTools::MakeCastPure(const FString& BlueprintPath, const FString& NodeName)
{
	const FString ObjPath = BlueprintPath.Contains(TEXT(".")) ? BlueprintPath : BlueprintPath + TEXT(".") + FPackageName::GetShortName(BlueprintPath);
	UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjPath);
	UK2Node_DynamicCast* CastNode = BP ? Cast<UK2Node_DynamicCast>(FindNodeByName(BP, NodeName)) : nullptr;
	if (!CastNode) { return FString::Printf(TEXT("ERROR no cast node %s"), *NodeName); }
	if (CastNode->IsNodePure()) { return FString::Printf(TEXT("SKIP %s already pure"), *NodeName); }
	TArray<UEdGraphPin*> Sources, Targets;
	if (UEdGraphPin* In = CastNode->GetExecPin()) { Sources = In->LinkedTo; }
	for (UEdGraphPin* Out : { CastNode->GetValidCastPin(), CastNode->GetInvalidCastPin() })
	{
		if (Out) { for (UEdGraphPin* T : Out->LinkedTo) { Targets.AddUnique(T); } }
	}
	CastNode->Modify();
	for (UEdGraphPin* P : Sources) { P->GetOwningNode()->Modify(); }
	for (UEdGraphPin* P : Targets) { P->GetOwningNode()->Modify(); }
	CastNode->SetPurity(true);
	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
	int32 Made = 0;
	for (UEdGraphPin* Src : Sources) { for (UEdGraphPin* Dst : Targets) { if (Schema->TryCreateConnection(Src, Dst)) { ++Made; } } }
	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	return FString::Printf(TEXT("OK %s pure, %d exec links rewired (%d in, %d out)%s"), *NodeName, Made, Sources.Num(), Targets.Num(),
		BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
}

FString UCDEditorTools::AddCallAfter(const FString& BlueprintPath, const FString& AfterNode, const FString& FunctionPath, const FString& PinDefaults)
{
	const FString ObjPath = BlueprintPath.Contains(TEXT(".")) ? BlueprintPath : BlueprintPath + TEXT(".") + FPackageName::GetShortName(BlueprintPath);
	UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *ObjPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	FString ClassPath, FuncName;
	if (!FunctionPath.Split(TEXT(":"), &ClassPath, &FuncName)) { return TEXT("ERROR FunctionPath needs Class:Function"); }
	UClass* FuncClass = LoadObject<UClass>(nullptr, *ClassPath);
	UFunction* Func = FuncClass ? FuncClass->FindFunctionByName(FName(*FuncName)) : nullptr;
	if (!Func) { return TEXT("ERROR no function"); }
	UEdGraph* Graph = nullptr;
	UEdGraphNode* After = FindNodeByName(BP, AfterNode, &Graph);
	UEdGraphPin* Then = After ? After->FindPin(UEdGraphSchema_K2::PN_Then, EGPD_Output) : nullptr;
	if (!Then) { return FString::Printf(TEXT("ERROR %s has no then pin"), *AfterNode); }
	TArray<UEdGraphPin*> OldTargets = Then->LinkedTo;
	for (UEdGraphPin* T : OldTargets)
	{
		if (const UK2Node_CallFunction* Prev = Cast<UK2Node_CallFunction>(T->GetOwningNode()))
		{
			if (Prev->GetTargetFunction() == Func) { return FString::Printf(TEXT("SKIP %s already followed by %s"), *AfterNode, *FuncName); }
		}
	}
	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
	Graph->Modify(); After->Modify();
	UK2Node_CallFunction* Call = NewObject<UK2Node_CallFunction>(Graph);
	Call->CreateNewGuid();
	Call->SetFromFunction(Func);
	Call->NodePosX = After->NodePosX + 260;
	Call->NodePosY = After->NodePosY + 200;
	Graph->AddNode(Call, false, false);
	Call->PostPlacedNewNode();
	Call->AllocateDefaultPins();
	UEdGraphPin* CallExec = Call->GetExecPin();
	UEdGraphPin* CallThen = Call->GetThenPin();
	if (!CallExec || !CallThen) { Graph->RemoveNode(Call); return TEXT("ERROR function is pure (no exec pins)"); }
	Then->BreakAllPinLinks();
	Schema->TryCreateConnection(Then, CallExec);
	for (UEdGraphPin* T : OldTargets) { Schema->TryCreateConnection(CallThen, T); }
	TArray<FString> Pairs;
	PinDefaults.ParseIntoArray(Pairs, TEXT(";"));
	FString Log;
	for (const FString& Pair : Pairs)
	{
		FString K, V;
		if (!Pair.Split(TEXT("="), &K, &V)) { continue; }
		if (UEdGraphPin* P = Call->FindPin(FName(*K.TrimStartAndEnd()), EGPD_Input)) { Schema->TrySetDefaultValue(*P, V.TrimStartAndEnd()); }
		else { Log += FString::Printf(TEXT(" [no pin %s]"), *K); }
	}
	FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	return FString::Printf(TEXT("OK %s: %s -> %s -> %d old targets%s%s"), *BP->GetName(), *AfterNode, *FuncName, OldTargets.Num(), *Log,
		BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
}

// CDEditorTools_HudAdditions.cpp - REVIEW DRAFT rev 5, 2026-11-06. Appended to Source/CastleDefenderEditor/Private/CDEditorTools.cpp
// (declarations go into CDEditorTools.h next to the existing tools; needs #include "K2Node_IfThenElse.h", "K2Node_Self.h",
// "K2Node_Event.h", "ScopedTransaction.h", "Editor.h"). Uses the existing helpers AllGraphs / FindNodeByName in that file.
//
// rev 2 (review): both tools are TRANSACTIONAL.
//   1. Plan + validate everything first (pins exist, directions, pin types compatible) - nothing is touched on a refusal.
//   2. Apply inside one FScopedTransaction (graph + every touched node Modify()'d, new nodes RF_Transactional).
//   3. Verify after the edit (links preserved by pin name, defaults unchanged, Blueprint compiles without error).
//   4. Any failure in 2 or 3: the transaction is undone (GEditor->UndoTransaction), the Blueprint is recompiled, the result
//      says "ERROR ... rolled back". A failed transformation leaves the original graph intact.
// rev 4 (second review): the rollback is VERIFIED, not asserted. A deterministic signature of every graph (nodes by GUID, class,
//   pins with direction, full type incl. ref/const, defaults, links as node GUID + pin name) is taken before the edit and again
//   after the undo. Equal -> "rolled back, graph verified unchanged". Different -> "ROLLBACK FAILED" with the first difference
//   and the instruction to restore the asset from its backup (the asset is left unsaved, nothing is written to disk).
//   Retarget compatibility now also requires the same by-reference and const flags (they change what the node may modify).
// rev 5 (third review): the signature also serialises PinValueType (map/set value terminal: category, sub-category, sub-object,
//   const, weak, UObject-wrapper) and each pin's index: pin ORDER is compared deliberately (node pins are not sorted).
//
// .h declarations:
//	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
//	static FString RetargetCallNodes(const FString& BlueprintPath, const FString& OldFunctionPath, const FString& NewFunctionPath);
//	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
//	static FString InsertNativeLayerSwitch(const FString& BlueprintPath, const FString& LayerName, const FString& DrawFunctionPath);

namespace
{
	UFunction* FindFunctionByPath(const FString& Path)
	{
		FString C, F;
		if (!Path.Split(TEXT(":"), &C, &F)) { return nullptr; }
		UClass* Cls = LoadObject<UClass>(nullptr, *C);
		return Cls ? Cls->FindFunctionByName(FName(*F)) : nullptr;
	}

	UBlueprint* LoadBP(const FString& Path)
	{
		return LoadObject<UBlueprint>(nullptr, *(Path.Contains(TEXT(".")) ? Path : Path + TEXT(".") + FPackageName::GetShortName(Path)));
	}

	// Same category / sub-category / sub-object / container / map value type, and (rev 4) the same by-reference and const flags:
	// a by-ref parameter may be modified by the callee, so a value pin silently becoming a reference changes behaviour.
	bool SamePinType(const FEdGraphPinType& A, const FEdGraphPinType& B)
	{
		return A.PinCategory == B.PinCategory && A.PinSubCategory == B.PinSubCategory && A.PinSubCategoryObject == B.PinSubCategoryObject
			&& A.ContainerType == B.ContainerType && A.PinValueType == B.PinValueType
			&& A.bIsReference == B.bIsReference && A.bIsConst == B.bIsConst;
	}

	// rev 4: deterministic text signature of all graphs of a Blueprint, one line per node, nodes and links sorted.
	TArray<FString> GraphSignature(UBlueprint* BP)
	{
		TArray<FString> Lines;
		for (UEdGraph* Graph : AllGraphs(BP))
		{
			if (!Graph) { continue; }
			for (UEdGraphNode* N : Graph->Nodes)
			{
				if (!N) { continue; }
				FString L = Graph->GetName() + TEXT("|") + N->NodeGuid.ToString() + TEXT("|") + N->GetClass()->GetName();
				if (const UK2Node_CallFunction* C = Cast<UK2Node_CallFunction>(N)) { L += TEXT("|fn=") + GetPathNameSafe(C->GetTargetFunction()); }
				for (int32 PinIndex = 0; PinIndex < N->Pins.Num(); ++PinIndex)   // rev 5: pin order is part of the signature
				{
					const UEdGraphPin* P = N->Pins[PinIndex];
					if (!P) { L += FString::Printf(TEXT("|#%d:null"), PinIndex); continue; }
					const FEdGraphPinType& T = P->PinType;
					const FEdGraphTerminalType& V = T.PinValueType;   // rev 5: map / set value type
					L += FString::Printf(TEXT("|#%d %s:%d:%s/%s/%s/%d/r%d/c%d/v{%s/%s/%s/c%d/w%d/u%d}=%s/%s/%s"), PinIndex, *P->PinName.ToString(), int32(P->Direction),
						*T.PinCategory.ToString(), *T.PinSubCategory.ToString(), *GetPathNameSafe(T.PinSubCategoryObject.Get()), int32(T.ContainerType),
						int32(T.bIsReference), int32(T.bIsConst),
						*V.TerminalCategory.ToString(), *V.TerminalSubCategory.ToString(), *GetPathNameSafe(V.TerminalSubCategoryObject.Get()),
						int32(V.bTerminalIsConst), int32(V.bTerminalIsWeakPointer), int32(V.bTerminalIsUObjectWrapper),
						*P->DefaultValue, *GetPathNameSafe(P->DefaultObject), *P->DefaultTextValue.ToString());
					TArray<FString> Links;
					for (const UEdGraphPin* To : P->LinkedTo) { if (To && To->GetOwningNode()) { Links.Add(To->GetOwningNode()->NodeGuid.ToString() + TEXT(".") + To->PinName.ToString()); } }
					Links.Sort();
					L += TEXT("->[") + FString::Join(Links, TEXT(",")) + TEXT("]");
				}
				Lines.Add(MoveTemp(L));
			}
		}
		Lines.Sort();
		return Lines;
	}

	// Undo the open-and-closed transaction, recompile, and PROVE the graph is back (rev 4): compare with the signature taken before.
	FString RollBack(UBlueprint* BP, const FString& Why, const TArray<FString>& Before)
	{
		const bool bUndone = GEditor && GEditor->UndoTransaction(false);
		FKismetEditorUtilities::CompileBlueprint(BP);
		const TArray<FString> After = GraphSignature(BP);
		if (bUndone && After == Before)
		{
			return FString::Printf(TEXT("ERROR %s: %s - rolled back, graph verified unchanged (%d nodes)%s"), *BP->GetName(), *Why, Before.Num(),
				BP->Status == BS_Error ? TEXT(" (Blueprint does not compile - it did not before the edit either?)") : TEXT(""));
		}
		FString Diff = TEXT("undo did not run");
		if (bUndone)
		{
			Diff = FString::Printf(TEXT("%d nodes before, %d after"), Before.Num(), After.Num());
			for (int32 i = 0; i < FMath::Max(Before.Num(), After.Num()); ++i)
			{
				const FString B = Before.IsValidIndex(i) ? Before[i] : TEXT("<none>");
				const FString A = After.IsValidIndex(i) ? After[i] : TEXT("<none>");
				if (A != B) { Diff += TEXT("; first difference: before ") + B.Left(300) + TEXT(" | after ") + A.Left(300); break; }
			}
		}
		UE_LOG(LogTemp, Error, TEXT("CDEditorTools: ROLLBACK FAILED on %s (%s): %s"), *BP->GetName(), *Why, *Diff);
		return FString::Printf(TEXT("ERROR %s: %s - ROLLBACK FAILED (%s). Do NOT save; restore the asset from its backup."), *BP->GetName(), *Why, *Diff);
	}
}

FString UCDEditorTools::RetargetCallNodes(const FString& BlueprintPath, const FString& OldFunctionPath, const FString& NewFunctionPath)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	UFunction* OldF = FindFunctionByPath(OldFunctionPath);
	UFunction* NewF = FindFunctionByPath(NewFunctionPath);
	if (!BP || !OldF || !NewF) { return TEXT("ERROR blueprint or function not found"); }
	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();

	// ---- 1. plan + validate (nothing touched yet) ----
	struct FPinRecord { FName Name; EEdGraphPinDirection Dir; TArray<UEdGraphPin*> Links; FString Default; UObject* DefaultObj; };
	struct FPlan { UK2Node_CallFunction* Call; TArray<FPinRecord> Pins; };
	TArray<FPlan> Plans;
	TArray<FString> Refused;
	for (UEdGraph* Graph : AllGraphs(BP))
	{
		if (!Graph) { continue; }
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node);
			if (!Call || Call->GetTargetFunction() != OldF) { continue; }
			FPlan Plan{ Call, {} };
			FString Why;
			for (UEdGraphPin* P : Call->Pins)
			{
				Plan.Pins.Add({ P->PinName, P->Direction, P->LinkedTo, P->DefaultValue, P->DefaultObject });
				if (P->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec || P->PinName == UEdGraphSchema_K2::PN_Self) { continue; }
				const FProperty* NewProp = NewF->FindPropertyByName(P->PinName);
				if (!NewProp) { if (P->LinkedTo.Num() || !P->bHidden) { Why = P->PinName.ToString() + TEXT(" missing"); } continue; }
				FEdGraphPinType NewType;
				Schema->ConvertPropertyToPinType(NewProp, NewType);
				const bool bNewIsOut = NewProp->HasAnyPropertyFlags(CPF_OutParm | CPF_ReturnParm) && !NewProp->HasAnyPropertyFlags(CPF_ReferenceParm);
				if ((P->Direction == EGPD_Output) != bNewIsOut) { Why = P->PinName.ToString() + TEXT(" direction differs"); break; }
				if (!SamePinType(P->PinType, NewType)) { Why = P->PinName.ToString() + TEXT(" type differs"); break; }
			}
			if (Why.IsEmpty()) { Plans.Add(MoveTemp(Plan)); } else { Refused.Add(Call->GetName() + TEXT(" (") + Why + TEXT(")")); }
		}
	}
	if (Plans.Num() == 0) { return FString::Printf(TEXT("OK %s: nothing to switch, %d refused %s"), *BP->GetName(), Refused.Num(), *FString::Join(Refused, TEXT(", "))); }

	// ---- 2. apply in one transaction ----
	const TArray<FString> Before = GraphSignature(BP);   // rev 4: for the rollback proof
	FString Failure;
	{
		FScopedTransaction Transaction(NSLOCTEXT("CDEditorTools", "Retarget", "CD Retarget Call Nodes"));
		BP->Modify();
		for (FPlan& Plan : Plans)
		{
			Plan.Call->GetGraph()->Modify();
			Plan.Call->Modify();
			for (FPinRecord& R : Plan.Pins) { for (UEdGraphPin* L : R.Links) { L->GetOwningNode()->Modify(); } }
			Plan.Call->SetFromFunction(NewF);
			Plan.Call->ReconstructNode();   // re-creates pins and moves links / defaults over by pin name
			// ---- 3a. verify this node: every recorded link and default survived ----
			for (const FPinRecord& R : Plan.Pins)
			{
				UEdGraphPin* Now = Plan.Call->FindPin(R.Name, R.Dir);
				if (!Now) { if (R.Links.Num()) { Failure = Plan.Call->GetName() + TEXT(".") + R.Name.ToString() + TEXT(" vanished"); } continue; }
				for (UEdGraphPin* L : R.Links) { if (!Now->LinkedTo.Contains(L)) { Failure = Plan.Call->GetName() + TEXT(".") + R.Name.ToString() + TEXT(" lost a link"); } }
				if (R.Links.Num() == 0 && (Now->DefaultValue != R.Default || Now->DefaultObject != R.DefaultObj)) { Failure = Plan.Call->GetName() + TEXT(".") + R.Name.ToString() + TEXT(" default changed"); }
			}
			if (!Failure.IsEmpty()) { break; }
		}
		if (Failure.IsEmpty())
		{
			FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
			FKismetEditorUtilities::CompileBlueprint(BP);
			if (BP->Status == BS_Error) { Failure = TEXT("Blueprint does not compile after the switch"); }   // 3b
		}
	}
	if (!Failure.IsEmpty()) { return RollBack(BP, Failure, Before); }
	return FString::Printf(TEXT("OK %s: %d switched, %d refused %s"), *BP->GetName(), Plans.Num(), Refused.Num(), *FString::Join(Refused, TEXT(", ")));
}

FString UCDEditorTools::InsertNativeLayerSwitch(const FString& BlueprintPath, const FString& LayerName, const FString& DrawFunctionPath)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }

	// ---- 1. plan + validate ----
	UK2Node_Event* Event = nullptr;
	UEdGraph* Graph = nullptr;
	for (UEdGraph* G : AllGraphs(BP))
	{
		if (!G) { continue; }
		for (UEdGraphNode* N : G->Nodes)
		{
			UK2Node_Event* E = Cast<UK2Node_Event>(N);
			if (E && E->GetFunctionName() == TEXT("ReceiveDrawHUD")) { if (Event) { return TEXT("ERROR more than one ReceiveDrawHUD event"); } Event = E; Graph = G; }
		}
	}
	if (!Event) { return TEXT("ERROR no Event ReceiveDrawHUD"); }
	UEdGraphPin* Then = Event->FindPin(UEdGraphSchema_K2::PN_Then, EGPD_Output);
	UEdGraphPin* SizeX = Event->FindPin(TEXT("SizeX"), EGPD_Output);
	UEdGraphPin* SizeY = Event->FindPin(TEXT("SizeY"), EGPD_Output);
	if (!Then || !SizeX || !SizeY) { return TEXT("ERROR event pins missing"); }
	if (Then->LinkedTo.Num() == 0) { return TEXT("ERROR draw event is empty"); }
	for (UEdGraphPin* T : Then->LinkedTo) { if (Cast<UK2Node_IfThenElse>(T->GetOwningNode())) { return TEXT("SKIP switch already present"); } }
	UFunction* DrawF = FindFunctionByPath(DrawFunctionPath);
	UFunction* UseF = FindFunctionByPath(TEXT("/Script/CastleDefender.CDHudLayers:UseNativeLayer"));
	if (!DrawF || !UseF) { return TEXT("ERROR draw function or UseNativeLayer not found"); }
	if (!DrawF->FindPropertyByName(TEXT("Hud")) || !DrawF->FindPropertyByName(TEXT("SizeX")) || !DrawF->FindPropertyByName(TEXT("SizeY"))) { return TEXT("ERROR draw function needs Hud, SizeX, SizeY"); }
	if (!UseF->FindPropertyByName(TEXT("Layer")) || !UseF->GetReturnProperty()) { return TEXT("ERROR UseNativeLayer signature"); }
	const TArray<UEdGraphPin*> OldNext = Then->LinkedTo;

	// ---- 2. apply in one transaction ----
	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
	const TArray<FString> Before = GraphSignature(BP);   // rev 4: for the rollback proof
	FString Failure;
	{
		FScopedTransaction Transaction(NSLOCTEXT("CDEditorTools", "LayerSwitch", "CD Insert Native Layer Switch"));
		BP->Modify(); Graph->Modify(); Event->Modify();
		for (UEdGraphPin* N : OldNext) { N->GetOwningNode()->Modify(); }
		auto Place = [&](UEdGraphNode* N, int32 DX, int32 DY)
		{
			N->SetFlags(RF_Transactional);
			N->CreateNewGuid(); N->NodePosX = Event->NodePosX + DX; N->NodePosY = Event->NodePosY + DY;
			Graph->AddNode(N, false, false); N->PostPlacedNewNode(); N->AllocateDefaultPins();
		};
		UK2Node_IfThenElse* Branch = NewObject<UK2Node_IfThenElse>(Graph);                                    Place(Branch, 260, -220);
		UK2Node_CallFunction* Use = NewObject<UK2Node_CallFunction>(Graph);  Use->SetFromFunction(UseF);      Place(Use, 260, -100);
		UK2Node_CallFunction* Draw = NewObject<UK2Node_CallFunction>(Graph); Draw->SetFromFunction(DrawF);    Place(Draw, 560, -320);
		UK2Node_Self* SelfNode = NewObject<UK2Node_Self>(Graph);                                                Place(SelfNode, 400, -420);

		auto Link = [&](UEdGraphPin* A, UEdGraphPin* B, const TCHAR* What) { if (Failure.IsEmpty() && !(A && B && Schema->TryCreateConnection(A, B))) { Failure = FString(TEXT("could not connect ")) + What; } };
		Then->BreakAllPinLinks();
		Link(Then, Branch->GetExecPin(), TEXT("event -> branch"));
		Link(Use->GetReturnValuePin(), Branch->GetConditionPin(), TEXT("UseNativeLayer -> condition"));
		if (UEdGraphPin* LP = Use->FindPin(TEXT("Layer"))) { Schema->TrySetDefaultValue(*LP, LayerName); if (LP->DefaultValue != LayerName) { Failure = TEXT("layer name not accepted"); } }
		Link(Branch->GetThenPin(), Draw->GetExecPin(), TEXT("branch true -> draw"));
		for (UEdGraphPin* N : OldNext) { Link(Branch->GetElsePin(), N, TEXT("branch false -> original graph")); }
		Link(SelfNode->FindPin(UEdGraphSchema_K2::PN_Self), Draw->FindPin(TEXT("Hud")), TEXT("self -> Hud"));
		Link(SizeX, Draw->FindPin(TEXT("SizeX")), TEXT("SizeX"));
		Link(SizeY, Draw->FindPin(TEXT("SizeY")), TEXT("SizeY"));
		// ---- 3. verify: the original graph hangs off False exactly as it hung off the event ----
		if (Failure.IsEmpty() && Branch->GetElsePin()->LinkedTo.Num() != OldNext.Num()) { Failure = TEXT("original graph not fully on False"); }
		if (Failure.IsEmpty())
		{
			FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
			FKismetEditorUtilities::CompileBlueprint(BP);
			if (BP->Status == BS_Error) { Failure = TEXT("Blueprint does not compile after the switch"); }
		}
	}
	if (!Failure.IsEmpty()) { return RollBack(BP, Failure, Before); }
	return FString::Printf(TEXT("OK %s: switch '%s' -> %s, original graph on False (%d links)"), *BP->GetName(), *LayerName, *DrawF->GetName(), OldNext.Num());
}

// Begin Object Name="X" ... CustomFunctionName="Y" pairs from a T3D graph text
static TMap<FString, FString> CDCustomEventNamesFromText(const FString& Text)
{
	TMap<FString, FString> Out; FString Cur;
	TArray<FString> Lines; Text.ParseIntoArrayLines(Lines);
	for (const FString& L : Lines)
	{
		const FString T = L.TrimStartAndEnd();
		if (T.StartsWith(TEXT("Begin Object")))
		{
			Cur.Empty();
			if (T.Contains(TEXT("K2Node_CustomEvent"))) { FParse::Value(*T, TEXT("Name="), Cur); Cur = Cur.TrimQuotes(); }
		}
		else if (!Cur.IsEmpty() && T.StartsWith(TEXT("CustomFunctionName=")))
		{
			FString V; FParse::Value(*T, TEXT("CustomFunctionName="), V); Out.Add(Cur, V.TrimQuotes());
		}
	}
	return Out;
}

FString UCDEditorTools::PasteGraphText(const FString& BlueprintPath, const FString& GraphName, const FString& TextFile, int32 OffsetX, int32 OffsetY, bool bReplaceAll)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	UEdGraph* Graph = nullptr;
	for (UEdGraph* G : AllGraphs(BP)) { if (G && G->GetName() == GraphName) { Graph = G; break; } }
	if (!Graph) { return FString::Printf(TEXT("ERROR no graph %s"), *GraphName); }
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *TextFile)) { return FString::Printf(TEXT("ERROR cannot read %s"), *TextFile); }
	if (Text.IsEmpty()) { return TEXT("ERROR empty paste file"); }
	if (!FEdGraphUtilities::CanImportNodesFromText(Graph, Text)) { return TEXT("ERROR the graph refuses this text (CanImportNodesFromText)"); }
	const int32 Before = Graph->Nodes.Num();
	TSet<UEdGraphNode*> Pasted;
	{
		FScopedTransaction Transaction(NSLOCTEXT("CDEditorTools", "PasteGraph", "CD Paste Graph Text"));
		BP->Modify(); Graph->Modify();
		if (bReplaceAll)
		{
			TArray<UEdGraphNode*> Old = Graph->Nodes;
			for (UEdGraphNode* N : Old) { if (N) { FBlueprintEditorUtils::RemoveNode(BP, N, true); } }
			// the skeleton class still lists the removed Custom Events; a pasted event with one of those names would be renamed
			// "CustomEvent_N" (11-06: Think / ResumeMove / HitStopEnd on BP_Zombie). Regenerate it first so the names are free.
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			FKismetEditorUtilities::GenerateBlueprintSkeleton(BP, true);
		}
		FEdGraphUtilities::ImportNodesFromText(Graph, Text, Pasted);
		FEdGraphUtilities::PostProcessPastedNodes(Pasted);
		// belt and braces: put back any Custom Event name the import changed
		{
			TMap<FString, FString> Wanted = CDCustomEventNamesFromText(Text);
			for (UEdGraphNode* N : Pasted)
			{
				UK2Node_CustomEvent* CE = Cast<UK2Node_CustomEvent>(N);
				const FString* Want = CE ? Wanted.Find(CE->GetName()) : nullptr;
				if (Want && !Want->IsEmpty() && CE->CustomFunctionName.ToString() != *Want)
				{
					UE_LOG(LogTemp, Warning, TEXT("[CDEditorTools] paste renamed Custom Event %s to %s; restoring %s"), *CE->GetName(), *CE->CustomFunctionName.ToString(), **Want);
					CE->Modify(); CE->CustomFunctionName = FName(**Want); CE->ReconstructNode();
				}
			}
		}
		for (UEdGraphNode* N : Pasted)
		{
			if (!N) { continue; }
			N->SetFlags(RF_Transactional);
			N->NodePosX += OffsetX; N->NodePosY += OffsetY;
			N->SnapToGrid(16);
		}
	}
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	return FString::Printf(TEXT("OK %s:%s pasted %d nodes, graph %d -> %d%s"), *BP->GetName(), *GraphName, Pasted.Num(), Before, Graph->Nodes.Num(),
		BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
}

TArray<FString> UCDEditorTools::ListGraphNodes(const FString& BlueprintPath, const FString& GraphName)
{
	TArray<FString> Out;
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { Out.Add(TEXT("ERROR no Blueprint")); return Out; }
	for (UEdGraph* G : AllGraphs(BP))
	{
		if (!G || G->GetName() != GraphName) { continue; }
		for (UEdGraphNode* N : G->Nodes) { if (N) { Out.Add(FString::Printf(TEXT("%s | %s | %s"), *N->GetName(), *N->GetClass()->GetName(), *N->GetNodeTitle(ENodeTitleType::ListView).ToString())); } }
	}
	return Out;
}

static bool CDParsePinType(const FString& Spec, FEdGraphPinType& Out, FString& Err)
{
	FString Cat; FParse::Value(*Spec, TEXT("PinCategory="), Cat); Cat = Cat.TrimQuotes();
	FString Sub; FParse::Value(*Spec, TEXT("PinSubCategory="), Sub); Sub = Sub.TrimQuotes();
	FString ObjPath;
	{
		int32 A = Spec.Find(TEXT("PinSubCategoryObject=\""));
		if (A != INDEX_NONE)
		{
			int32 Q1 = Spec.Find(TEXT("'"), ESearchCase::CaseSensitive, ESearchDir::FromStart, A);
			int32 Q2 = Q1 == INDEX_NONE ? INDEX_NONE : Spec.Find(TEXT("'"), ESearchCase::CaseSensitive, ESearchDir::FromStart, Q1 + 1);
			if (Q1 != INDEX_NONE && Q2 != INDEX_NONE) { ObjPath = Spec.Mid(Q1 + 1, Q2 - Q1 - 1); }
		}
	}
	Out = FEdGraphPinType();
	if (Cat == TEXT("bool")) { Out.PinCategory = UEdGraphSchema_K2::PC_Boolean; }
	else if (Cat == TEXT("int")) { Out.PinCategory = UEdGraphSchema_K2::PC_Int; }
	else if (Cat == TEXT("int64")) { Out.PinCategory = UEdGraphSchema_K2::PC_Int64; }
	else if (Cat == TEXT("real")) { Out.PinCategory = UEdGraphSchema_K2::PC_Real; Out.PinSubCategory = Sub == TEXT("float") ? UEdGraphSchema_K2::PC_Float : UEdGraphSchema_K2::PC_Double; }
	else if (Cat == TEXT("string")) { Out.PinCategory = UEdGraphSchema_K2::PC_String; }
	else if (Cat == TEXT("name")) { Out.PinCategory = UEdGraphSchema_K2::PC_Name; }
	else if (Cat == TEXT("text")) { Out.PinCategory = UEdGraphSchema_K2::PC_Text; }
	else if (Cat == TEXT("struct"))
	{
		UScriptStruct* St = LoadObject<UScriptStruct>(nullptr, *ObjPath);
		if (!St) { Err = TEXT("struct not found ") + ObjPath; return false; }
		Out.PinCategory = UEdGraphSchema_K2::PC_Struct; Out.PinSubCategoryObject = St;
	}
	else if (Cat == TEXT("object") || Cat == TEXT("class") || Cat == TEXT("softobject"))
	{
		UClass* Cls = LoadObject<UClass>(nullptr, *ObjPath);
		if (!Cls) { Err = TEXT("class not found ") + ObjPath; return false; }
		Out.PinCategory = Cat == TEXT("class") ? UEdGraphSchema_K2::PC_Class : (Cat == TEXT("softobject") ? UEdGraphSchema_K2::PC_SoftObject : UEdGraphSchema_K2::PC_Object);
		Out.PinSubCategoryObject = Cls;
	}
	else { Err = TEXT("unsupported PinCategory ") + Cat; return false; }
	if (Spec.Contains(TEXT("ContainerType=Array"))) { Out.ContainerType = EPinContainerType::Array; }
	return true;
}

FString UCDEditorTools::AddMemberVariable(const FString& BlueprintPath, const FString& VarName, const FString& TypeSpec)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	const FName Name(*VarName);
	if (FBlueprintEditorUtils::FindNewVariableIndex(BP, Name) != INDEX_NONE) { return TEXT("SKIP exists"); }
	FEdGraphPinType Type; FString Err;
	if (!CDParsePinType(TypeSpec, Type, Err)) { return TEXT("ERROR ") + Err; }
	BP->Modify();
	return FBlueprintEditorUtils::AddMemberVariable(BP, Name, Type) ? TEXT("OK") : TEXT("ERROR AddMemberVariable refused");
}

FString UCDEditorTools::RemoveMemberVariable(const FString& BlueprintPath, const FString& VarName)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	const FName Name(*VarName);
	if (FBlueprintEditorUtils::FindNewVariableIndex(BP, Name) == INDEX_NONE) { return TEXT("SKIP missing"); }
	BP->Modify();
	FBlueprintEditorUtils::RemoveMemberVariable(BP, Name);
	return TEXT("OK");
}

FString UCDEditorTools::RefreshAllNodes(const FString& BlueprintPath)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	int32 N = 0;
	for (UEdGraph* G : AllGraphs(BP))
	{
		if (!G) { continue; }
		const UEdGraphSchema* Schema = G->GetSchema();
		TArray<UEdGraphNode*> Nodes = G->Nodes;
		for (UEdGraphNode* Node : Nodes) { if (Node && Schema) { Schema->ReconstructNode(*Node); ++N; } }
	}
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	return FString::Printf(TEXT("OK %d nodes refreshed%s"), N, BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
}

FString UCDEditorTools::RenameCustomEvent(const FString& BlueprintPath, const FString& GraphName, const FString& NodeName, const FString& NewName)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	for (UEdGraph* G : AllGraphs(BP))
	{
		if (!G || G->GetName() != GraphName) { continue; }
		for (UEdGraphNode* N : G->Nodes)
		{
			UK2Node_CustomEvent* CE = Cast<UK2Node_CustomEvent>(N);
			if (!CE || CE->GetName() != NodeName) { continue; }
			const FString OldName = CE->CustomFunctionName.ToString();
			if (OldName == NewName) { return FString::Printf(TEXT("OK %s already %s"), *NodeName, *NewName); }
			const FScopedTransaction Transaction(NSLOCTEXT("CDEditorTools", "RenameEvent", "CD Rename Custom Event"));
			BP->Modify(); CE->Modify();
			CE->CustomFunctionName = FName(*NewName); CE->ReconstructNode();
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			FKismetEditorUtilities::CompileBlueprint(BP);
			return FString::Printf(TEXT("OK %s: %s -> %s%s"), *NodeName, *OldName, *NewName, BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
		}
	}
	return FString::Printf(TEXT("ERROR no Custom Event node %s in %s"), *NodeName, *GraphName);
}

FString UCDEditorTools::RestoreCustomEventNames(const FString& BlueprintPath, const FString& GraphName, const FString& TextFile)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *TextFile)) { return FString::Printf(TEXT("ERROR cannot read %s"), *TextFile); }
	const TMap<FString, FString> Wanted = CDCustomEventNamesFromText(Text);
	FString Out; int32 Changed = 0;
	for (UEdGraph* G : AllGraphs(BP))
	{
		if (!G || G->GetName() != GraphName) { continue; }
		const FScopedTransaction Transaction(NSLOCTEXT("CDEditorTools", "RestoreEvents", "CD Restore Custom Event Names"));
		BP->Modify();
		for (UEdGraphNode* N : G->Nodes)
		{
			UK2Node_CustomEvent* CE = Cast<UK2Node_CustomEvent>(N);
			const FString* Want = CE ? Wanted.Find(CE->GetName()) : nullptr;
			if (!Want || Want->IsEmpty()) { continue; }
			if (CE->CustomFunctionName.ToString() == *Want) { Out += FString::Printf(TEXT("= %s is %s\n"), *CE->GetName(), **Want); continue; }
			Out += FString::Printf(TEXT("~ %s: %s -> %s\n"), *CE->GetName(), *CE->CustomFunctionName.ToString(), **Want);
			CE->Modify(); CE->CustomFunctionName = FName(**Want); CE->ReconstructNode(); ++Changed;
		}
	}
	if (Changed > 0) { FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); FKismetEditorUtilities::CompileBlueprint(BP); }
	return Out + FString::Printf(TEXT("OK %d renamed%s"), Changed, BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
}

FString UCDEditorTools::SetComponentSocket(const FString& BlueprintPath, const FString& ComponentName, const FString& SocketName)
{
	UBlueprint* BP = LoadBP(BlueprintPath);
	if (!BP) { return TEXT("ERROR no Blueprint"); }
	if (!BP->SimpleConstructionScript) { return TEXT("ERROR no construction script"); }
	for (USCS_Node* N : BP->SimpleConstructionScript->GetAllNodes())
	{
		if (!N || N->GetVariableName() != FName(*ComponentName)) { continue; }
		const FScopedTransaction Transaction(NSLOCTEXT("CDEditorTools", "SetSocket", "CD Set Component Socket"));
		BP->Modify(); N->Modify();
		N->AttachToName = FName(*SocketName);
		if (USceneComponent* Tpl = Cast<USceneComponent>(N->ComponentTemplate)) { Tpl->Modify(); Tpl->SetupAttachment(Tpl->GetAttachParent(), FName(*SocketName)); }
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
		FKismetEditorUtilities::CompileBlueprint(BP);
		return FString::Printf(TEXT("OK %s -> %s%s"), *ComponentName, *SocketName, BP->Status == BS_Error ? TEXT(" (COMPILE ERROR)") : TEXT(""));
	}
	return FString::Printf(TEXT("ERROR no component %s in %s"), *ComponentName, *BP->GetName());
}
