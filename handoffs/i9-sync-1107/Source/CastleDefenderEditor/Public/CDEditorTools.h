// #500 point 7: editor checks as one click / one line. From Python:
//   unreal.CDEditorTools.find_blueprints_with_errors('/Game/CastleDefender', True)   # True = recompile each Blueprint first
//   unreal.CDEditorTools.find_expensive_calls('/Game/CastleDefender')
// Each returns readable lines ("BP_X | EventGraph | K2Node_CallFunction_7 | GetAllActorsWithTag"), also printed to the Output Log.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDEditorTools.generated.h"

UCLASS()
class CASTLEDEFENDEREDITOR_API UCDEditorTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// Blueprints under Path whose compile status is Error or that have nodes with errors.
	// bRecompile = true compiles each one first (slow on big folders; nothing is saved, BUT the in-memory Blueprints are changed: run it on a
	// clean editor, never with unsaved Blueprint work open). false = the status from the last compile.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Checks", meta = (DevelopmentOnly))
	static TArray<FString> FindBlueprintsWithErrors(const FString& Path = TEXT("/Game/CastleDefender"), bool bRecompile = false);

	// Every call to a known-expensive function in any Blueprint graph under Path (world scans, traces, widget scans).
	// A call on Tick / DrawHUD / a short timer is a frame-rate problem; on BeginPlay or an event it is usually fine.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Checks", meta = (DevelopmentOnly))
	static TArray<FString> FindExpensiveCalls(const FString& Path = TEXT("/Game/CastleDefender"));

	// Balance tuning: set the literal default of one input pin on one graph node (node names as CDDumpBlueprint prints them,
	// e.g. "K2Node_CallFunction_PH7", pin "B", value "300.0"). Compiles the Blueprint; does NOT save (save it yourself).
	// Returns "OK <node>.<pin>: <old> -> <new>" or "ERROR ...". Unlinked pins only: a pin fed by a wire has no literal to change.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString SetNodePinDefault(const FString& BlueprintPath, const FString& NodeName, const FString& PinName, const FString& NewValue, bool bCompile = true);

	// Insert a call to a static function in front of an input pin: whatever fed TargetNode.TargetPin now feeds the function's FIRST
	// input, and the function's ReturnValue feeds TargetNode.TargetPin. ExtraArgPin ("Soldier") is wired from ExtraSource
	// ("CX_3884.ReturnValue"; empty = leave unwired). FunctionPath e.g. "/Script/CastleDefender.CDSoldierPromptLibrary:GateSoldierPrompt".
	// Compiles, does NOT save. Refuses if TargetPin already comes from a node calling the same function (no double insert).
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString InsertPinFilter(const FString& BlueprintPath, const FString& TargetNode, const FString& TargetPin, const FString& FunctionPath,
		const FString& ExtraArgPin, const FString& ExtraSource);

	// Wire one output pin to one input pin ("CX_3884.ReturnValue" -> "K2Node_CallFunction_5.Soldier"). Compiles, does NOT save.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString ConnectPins(const FString& BlueprintPath, const FString& FromNodeDotPin, const FString& ToNodeDotPin);

	// Name of the node that feeds NodeName.PinName (input), "" if unwired. Lets scripts find nodes InsertPinFilter created.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString GetPinSource(const FString& BlueprintPath, const FString& NodeName, const FString& PinName);

	// Turn an impure "Cast To X" node pure (it then evaluates whenever its output is read, e.g. inside a draw loop) and keep the
	// execution flow: whatever executed the cast now executes the nodes its Then / CastFailed pins led to. Compiles, does NOT save.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString MakeCastPure(const FString& BlueprintPath, const FString& NodeName);

	// Add a call to a static/BlueprintCallable function right after AfterNode's "then" exec pin: AfterNode -> new call -> whatever
	// AfterNode led to before. PinDefaults "Location=(X=40,Y=1750,Z=200);Count=10" sets literals. Compiles, does NOT save.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString AddCallAfter(const FString& BlueprintPath, const FString& AfterNode, const FString& FunctionPath, const FString& PinDefaults);
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString RetargetCallNodes(const FString& BlueprintPath, const FString& OldFunctionPath, const FString& NewFunctionPath);

	// Headless Ctrl+V (11-06): import a T3D graph text file (a hand-off paste) into one graph of a Blueprint, exactly like
	// pasting it in the editor (FEdGraphUtilities::ImportNodesFromText + PostProcessPastedNodes), shifted by OffsetX/Y.
	// bReplaceAll = Ctrl+A, Delete first (applyall "merged" files). Compiles, does NOT save. Returns "OK <pasted> nodes,
	// graph <n> -> <m>" or "ERROR ...". Nothing is touched on an ERROR before the import.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString PasteGraphText(const FString& BlueprintPath, const FString& GraphName, const FString& TextFile, int32 OffsetX = 0, int32 OffsetY = 0, bool bReplaceAll = false);

	// Blueprint member variables from a hand-off "BPVar(...)" line (11-06). TypeSpec = the VarType=(...) text:
	// PinCategory bool|int|real(double)|struct(Vector...)|object(Class path or BlueprintGeneratedClass path), ContainerType=Array.
	// Returns "OK" / "SKIP exists" / "ERROR ...". Does not compile or save.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString AddMemberVariable(const FString& BlueprintPath, const FString& VarName, const FString& TypeSpec);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString RemoveMemberVariable(const FString& BlueprintPath, const FString& VarName);

	// Refresh every node of every graph (like "Refresh All Nodes"), then compile.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString RefreshAllNodes(const FString& BlueprintPath);

	// 11-06: a pasted Custom Event whose name still exists in the (stale) skeleton class gets renamed "CustomEvent_N" by the paste.
	// RenameCustomEvent sets one event's name back (node names as ListGraphNodes prints them). Compiles, does NOT save.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString RenameCustomEvent(const FString& BlueprintPath, const FString& GraphName, const FString& NodeName, const FString& NewName);

	// Read every K2Node_CustomEvent's CustomFunctionName from a T3D text (the file that was pasted, or an older export) and set the
	// same-named live nodes back to those names. Returns one line per change plus "OK n renamed". Compiles, does NOT save.
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString RestoreCustomEventNames(const FString& BlueprintPath, const FString& GraphName, const FString& TextFile);

	// Attach a Blueprint component template to a socket/bone of its parent (the Details "Parent Socket" field; Python cannot reach it).
	// Compiles, does NOT save. Returns "OK <component> -> <socket>" or "ERROR ...".
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString SetComponentSocket(const FString& BlueprintPath, const FString& ComponentName, const FString& SocketName);

	// Node names of one graph, one per line "Name | Class | Title" (to find pasted nodes and check a paste landed).
	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static TArray<FString> ListGraphNodes(const FString& BlueprintPath, const FString& GraphName);

	UFUNCTION(BlueprintCallable, Category = "Castle Defender|Tuning", meta = (DevelopmentOnly))
	static FString InsertNativeLayerSwitch(const FString& BlueprintPath, const FString& LayerName, const FString& DrawFunctionPath);
};
