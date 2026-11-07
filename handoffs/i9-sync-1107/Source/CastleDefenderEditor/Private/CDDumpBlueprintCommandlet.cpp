#include "CDDumpBlueprintCommandlet.h"
#include "Components/PrimitiveComponent.h"
#include "EdGraph/EdGraph.h"
#include "Engine/Blueprint.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "GameFramework/Character.h"
#include "K2Node_CallFunction.h"
#include "K2Node_Variable.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "K2Node.h"
#include "K2Node_DynamicCast.h"
#include "K2Node_MacroInstance.h"
#include "K2Node_Event.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_FunctionEntry.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"

namespace CDDumpJson
{
	// Typed, untruncated dump for the BP->C++ translator (2026-11-05). One object per Blueprint: graphs -> nodes -> pins.
	static TSharedRef<FJsonObject> PinJson(const UEdGraphPin* Pin)
	{
		TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
		J->SetStringField(TEXT("name"), Pin->PinName.ToString());
		J->SetStringField(TEXT("dir"), Pin->Direction == EGPD_Input ? TEXT("in") : TEXT("out"));
		J->SetStringField(TEXT("cat"), Pin->PinType.PinCategory.ToString());
		J->SetStringField(TEXT("subcat"), Pin->PinType.PinSubCategory.ToString());
		J->SetStringField(TEXT("subobj"), Pin->PinType.PinSubCategoryObject.IsValid() ? Pin->PinType.PinSubCategoryObject->GetPathName() : FString());
		J->SetNumberField(TEXT("container"), (int32)Pin->PinType.ContainerType);
		J->SetBoolField(TEXT("ref"), Pin->PinType.bIsReference);
		J->SetBoolField(TEXT("const"), Pin->PinType.bIsConst);
		J->SetBoolField(TEXT("hidden"), Pin->bHidden);
		J->SetStringField(TEXT("default"), Pin->DefaultValue);
		J->SetStringField(TEXT("defaultObj"), Pin->DefaultObject ? Pin->DefaultObject->GetPathName() : FString());
		J->SetStringField(TEXT("defaultText"), Pin->DefaultTextValue.ToString());
		TArray<TSharedPtr<FJsonValue>> Links;
		for (const UEdGraphPin* L : Pin->LinkedTo) { Links.Add(MakeShared<FJsonValueString>(L->GetOwningNode()->GetName() + TEXT(".") + L->PinName.ToString())); }
		J->SetArrayField(TEXT("links"), Links);
		return J;
	}

	static TSharedRef<FJsonObject> NodeJson(const UEdGraphNode* Node)
	{
		TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
		J->SetStringField(TEXT("name"), Node->GetName());
		J->SetStringField(TEXT("class"), Node->GetClass()->GetName());
		J->SetStringField(TEXT("title"), Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
		if (const UK2Node* K = Cast<UK2Node>(Node)) { J->SetBoolField(TEXT("pure"), K->IsNodePure()); }
		if (const UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node))
		{
			const UFunction* Fn = Call->GetTargetFunction();
			J->SetStringField(TEXT("func"), Fn ? Fn->GetName() : Call->FunctionReference.GetMemberName().ToString());
			J->SetStringField(TEXT("funcOwner"), Fn && Fn->GetOwnerClass() ? Fn->GetOwnerClass()->GetPathName() : FString());
			J->SetBoolField(TEXT("static"), Fn && Fn->HasAnyFunctionFlags(FUNC_Static));
			J->SetBoolField(TEXT("native"), Fn && Fn->HasAnyFunctionFlags(FUNC_Native));
			J->SetBoolField(TEXT("latent"), Fn && Fn->HasMetaData(TEXT("Latent")));
		}
		if (const UK2Node_Variable* Var = Cast<UK2Node_Variable>(Node))
		{
			J->SetStringField(TEXT("var"), Var->GetVarNameString());
			const UClass* Owner = Var->VariableReference.GetMemberParentClass(Var->GetBlueprintClassFromNode());
			J->SetStringField(TEXT("varOwner"), Owner ? Owner->GetPathName() : FString());
			J->SetBoolField(TEXT("varSelf"), Var->VariableReference.IsSelfContext());
		}
		if (const UK2Node_DynamicCast* C = Cast<UK2Node_DynamicCast>(Node))
		{
			J->SetStringField(TEXT("castTo"), C->TargetType ? C->TargetType->GetPathName() : FString());
		}
		if (const UK2Node_MacroInstance* M = Cast<UK2Node_MacroInstance>(Node))
		{
			J->SetStringField(TEXT("macro"), M->GetMacroGraph() ? M->GetMacroGraph()->GetName() : FString());
		}
		if (const UK2Node_Event* E = Cast<UK2Node_Event>(Node))
		{
			J->SetStringField(TEXT("event"), E->GetFunctionName().ToString());
			J->SetBoolField(TEXT("custom"), Node->IsA<UK2Node_CustomEvent>());
		}
		TArray<TSharedPtr<FJsonValue>> Pins;
		for (const UEdGraphPin* Pin : Node->Pins) { Pins.Add(MakeShared<FJsonValueObject>(PinJson(Pin))); }
		J->SetArrayField(TEXT("pins"), Pins);
		return J;
	}
}

int32 UCDDumpBlueprintCommandlet::Main(const FString& Params)
{
	FString AssetsArg, Out;
	FParse::Value(*Params, TEXT("assets="), AssetsArg, false);
	FParse::Value(*Params, TEXT("out="), Out);
	FString JsonOut;
	FParse::Value(*Params, TEXT("json="), JsonOut);   // optional: typed full dump for the translator
	TArray<TSharedPtr<FJsonValue>> JsonBPs;
	TArray<FString> Paths, Lines;
	AssetsArg.ParseIntoArray(Paths, TEXT(","));
	for (const FString& PathIn : Paths)
	{
		const FString Path = PathIn.TrimStartAndEnd();
		UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *(Path + TEXT(".") + FPackageName::GetShortName(Path)));
		if (!BP)
		{
			Lines.Add(TEXT("missing ") + Path);
			continue;
		}
		Lines.Add(FString::Printf(TEXT("##### %s parent %s"), *BP->GetName(), BP->ParentClass ? *BP->ParentClass->GetName() : TEXT("?")));
		if (UClass* Gen = BP->GeneratedClass)
		{
			// Collision of every primitive component on the class default (native and Blueprint-added).
			TArray<UObject*> Templates;
			if (const ACharacter* CDO = Cast<ACharacter>(Gen->GetDefaultObject()))
			{
				TInlineComponentArray<UPrimitiveComponent*> Prims;
				CDO->GetComponents(Prims);
				for (UPrimitiveComponent* P : Prims) { Templates.Add(P); }
			}
			if (BP->SimpleConstructionScript)
			{
				for (USCS_Node* N : BP->SimpleConstructionScript->GetAllNodes()) { if (N && N->ComponentTemplate) { Templates.Add(N->ComponentTemplate); } }
			}
			for (UObject* T : Templates)
			{
				if (const UPrimitiveComponent* P = Cast<UPrimitiveComponent>(T))
				{
					Lines.Add(FString::Printf(TEXT("  COMPONENT %s (%s) collision %d profile %s overlaps %d"), *P->GetName(), *P->GetClass()->GetName(),
						(int32)P->GetCollisionEnabled(), *P->GetCollisionProfileName().ToString(), P->GetGenerateOverlapEvents()));
				}
			}
		}
		TArray<UEdGraph*> Graphs;
		BP->GetAllGraphs(Graphs);
		if (!JsonOut.IsEmpty())
		{
			TSharedRef<FJsonObject> JB = MakeShared<FJsonObject>();
			JB->SetStringField(TEXT("name"), BP->GetName());
			JB->SetStringField(TEXT("path"), BP->GetPathName());
			JB->SetStringField(TEXT("parent"), BP->ParentClass ? BP->ParentClass->GetPathName() : FString());
			JB->SetStringField(TEXT("generated"), BP->GeneratedClass ? BP->GeneratedClass->GetPathName() : FString());
			TArray<TSharedPtr<FJsonValue>> JG;
			for (UEdGraph* Graph : Graphs)
			{
				TSharedRef<FJsonObject> G = MakeShared<FJsonObject>();
				G->SetStringField(TEXT("name"), Graph->GetName());
				TArray<TSharedPtr<FJsonValue>> JN;
				for (UEdGraphNode* Node : Graph->Nodes) { if (Node) { JN.Add(MakeShared<FJsonValueObject>(CDDumpJson::NodeJson(Node))); } }
				G->SetArrayField(TEXT("nodes"), JN);
				JG.Add(MakeShared<FJsonValueObject>(G));
			}
			JB->SetArrayField(TEXT("graphs"), JG);
			TArray<TSharedPtr<FJsonValue>> JV;
			for (const FBPVariableDescription& V : BP->NewVariables)
			{
				TSharedRef<FJsonObject> VJ = MakeShared<FJsonObject>();
				VJ->SetStringField(TEXT("name"), V.VarName.ToString());
				VJ->SetStringField(TEXT("cat"), V.VarType.PinCategory.ToString());
				VJ->SetStringField(TEXT("subobj"), V.VarType.PinSubCategoryObject.IsValid() ? V.VarType.PinSubCategoryObject->GetPathName() : FString());
				VJ->SetNumberField(TEXT("container"), (int32)V.VarType.ContainerType);
				JV.Add(MakeShared<FJsonValueObject>(VJ));
			}
			JB->SetArrayField(TEXT("variables"), JV);
			JsonBPs.Add(MakeShared<FJsonValueObject>(JB));
		}
		for (UEdGraph* Graph : Graphs)
		{
			Lines.Add(FString::Printf(TEXT("== graph %s (%d nodes)"), *Graph->GetName(), Graph->Nodes.Num()));
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (!Node) { continue; }
				FString What;
				if (const UK2Node_CallFunction* Call = Cast<UK2Node_CallFunction>(Node))
				{
					const UFunction* Fn = Call->GetTargetFunction();
					What = FString::Printf(TEXT("CALL %s::%s"), Fn && Fn->GetOwnerClass() ? *Fn->GetOwnerClass()->GetName() : TEXT("?"), Fn ? *Fn->GetName() : *Call->FunctionReference.GetMemberName().ToString());
				}
				else if (const UK2Node_Variable* Var = Cast<UK2Node_Variable>(Node))
				{
					What = FString::Printf(TEXT("VAR %s"), *Var->GetVarNameString());
				}
				else
				{
					What = Node->GetClass()->GetName();
				}
				FString Links;
				for (const UEdGraphPin* Pin : Node->Pins)
				{
					if (Pin->LinkedTo.Num() == 0 && (Pin->DefaultValue.IsEmpty() && !Pin->DefaultObject)) { continue; }
					Links += FString::Printf(TEXT(" [%s%s"), Pin->Direction == EGPD_Input ? TEXT("<") : TEXT(">"), *Pin->PinName.ToString());
					if (!Pin->DefaultValue.IsEmpty()) { Links += TEXT("=") + Pin->DefaultValue.Left(40); }
					if (Pin->DefaultObject) { Links += TEXT("=") + Pin->DefaultObject->GetName(); }
					for (const UEdGraphPin* L : Pin->LinkedTo) { Links += TEXT(" ") + L->GetOwningNode()->GetName() + TEXT(".") + L->PinName.ToString(); }
					Links += TEXT("]");
				}
				Lines.Add(FString::Printf(TEXT("  %s | %s | %s |%s"), *Node->GetName(), *What, *Node->GetNodeTitle(ENodeTitleType::ListView).ToString().Replace(TEXT("\n"), TEXT(" ")), *Links));
			}
		}
	}
	if (!Out.IsEmpty()) { FFileHelper::SaveStringArrayToFile(Lines, *Out); }
	if (!JsonOut.IsEmpty())
	{
		FString Str;
		const TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Str);
		FJsonSerializer::Serialize(JsonBPs, W);
		FFileHelper::SaveStringToFile(Str, *JsonOut, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	}
	return 0;
}
