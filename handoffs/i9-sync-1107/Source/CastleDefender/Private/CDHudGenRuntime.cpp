// CDHudGenRuntime.cpp - REVIEW DRAFT rev 5, 2026-11-06 (see CDHudGenRuntime.h)
#include "CDHudGenRuntime.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Subsystems/LocalPlayerSubsystem.h"
#include "TimerManager.h"
#include "UObject/UObjectGlobals.h"

namespace CDGen
{
	void ErrorOnce(const void* Site, const FString& Msg)
	{
		static TSet<const void*> Logged;
		if (!Logged.Contains(Site)) { Logged.Add(Site); UE_LOG(LogTemp, Error, TEXT("cd.HudGen: %s"), *Msg); }
	}

	// rev 5: keyed by the site string's VALUE (generated sites are unique strings), so literal pooling can neither merge nor split sites
	void ErrorOnceText(const TCHAR* Site, const FString& Msg)
	{
		static TSet<FString> Logged;
		const FString Key(Site ? Site : TEXT("?"));
		if (!Logged.Contains(Key)) { Logged.Add(Key); UE_LOG(LogTemp, Error, TEXT("cd.HudGen: %s"), *Msg); }
	}

	// ---- reflection epoch: bumped on reinstancing (editor Blueprint recompile, hot reload, live coding) ----
	static uint32 GEpoch = 1;
	uint32 ReflectionEpoch()
	{
		static bool bHooked = false;
		if (!bHooked)
		{
			bHooked = true;
#if WITH_EDITOR
			FCoreUObjectDelegates::OnObjectsReinstanced.AddLambda([](const TMap<UObject*, UObject*>&) { ++GEpoch; });
#endif
			FCoreUObjectDelegates::ReloadCompleteDelegate.AddLambda([](EReloadCompleteReason) { ++GEpoch; });
		}
		return GEpoch;
	}

	FString DescribeMismatch(const FProperty* P, const TCHAR* Wanted)
	{
		return FString::Printf(TEXT("type mismatch at %s: property %s is %s (%s) - access refused"), Wanted,
			P ? *P->GetName() : TEXT("?"), P ? *P->GetClass()->GetName() : TEXT("?"), P ? *P->GetCPPType() : TEXT("?"));
	}

	UObject* LoadAssetByPath(const TCHAR* Path)
	{
		UObject* O = StaticLoadObject(UObject::StaticClass(), nullptr, Path);
		if (!O) { ErrorOnce(Path, FString::Printf(TEXT("asset missing: %s"), Path)); }
		return O;
	}

	UClass* LoadClassByPath(const TCHAR* Path)
	{
		UClass* C = StaticLoadClass(UObject::StaticClass(), nullptr, Path);
		if (!C) { ErrorOnce(Path, FString::Printf(TEXT("class missing: %s"), Path)); }
		return C;
	}

	int64 EnumValue(const TCHAR* EnumPath, const TCHAR* ValueName)
	{
		const UEnum* E = FindObject<UEnum>(nullptr, EnumPath);
		if (!E) { E = LoadObject<UEnum>(nullptr, EnumPath); }
		const int64 V = E ? E->GetValueByNameString(ValueName) : INDEX_NONE;
		if (V == INDEX_NONE) { ErrorOnce(ValueName, FString::Printf(TEXT("enum value %s::%s missing"), EnumPath, ValueName)); return 0; }
		return V;
	}

	FProperty* FindProp(FPropSite& Site, const UObject* Obj, FName Name)
	{
		const UClass* Cls = Obj->GetClass();
		const uint32 Epoch = ReflectionEpoch();
		if (Site.Class != Cls || Site.Epoch != Epoch)
		{
			Site.Class = Cls;
			Site.Epoch = Epoch;
			Site.Prop = FindFProperty<FProperty>(Cls, Name);
			if (!Site.Prop) { ErrorOnce(&Site, FString::Printf(TEXT("%s has no property %s"), *Cls->GetName(), *Name.ToString())); }
		}
		return Site.Prop;
	}

	FCall::FCall(FFuncSite& Site, UObject* InTarget, FName FuncName, const TCHAR* OwnerClassPath)
		: SiteKey(&Site)
	{
		UClass* Cls = nullptr;
		if (OwnerClassPath) { Cls = StaticLoadClass(UObject::StaticClass(), nullptr, OwnerClassPath); InTarget = Cls ? Cls->GetDefaultObject() : nullptr; }
		else if (InTarget) { Cls = InTarget->GetClass(); }
		if (!InTarget || !Cls) { return; }   // Blueprint: calling on None does nothing (it logs "Accessed None"; we stay quiet per frame)
		const uint32 Epoch = ReflectionEpoch();
		if (Site.Class != Cls || Site.Epoch != Epoch)
		{
			Site.Class = Cls;
			Site.Epoch = Epoch;
			Site.Func = Cls->FindFunctionByName(FuncName);
			if (!Site.Func) { ErrorOnce(&Site, FString::Printf(TEXT("%s has no function %s"), *Cls->GetName(), *FuncName.ToString())); }
		}
		Func = Site.Func;
		Target = InTarget;
		if (Func)
		{
			Buffer = static_cast<uint8*>(FMemory::Malloc(FMath::Max<int32>(1, Func->ParmsSize), 16));
			FMemory::Memzero(Buffer, Func->ParmsSize);
			Func->InitializeStruct(Buffer);
		}
	}

	FCall::~FCall()
	{
		if (Buffer && Func) { Func->DestroyStruct(Buffer); }
		if (Buffer) { FMemory::Free(Buffer); }
	}

	FProperty* FCall::Param(FName Pin) const
	{
		if (!Func) { return nullptr; }
		FProperty* P = Func->FindPropertyByName(Pin);
		if (!P || !P->HasAnyPropertyFlags(CPF_Parm)) { ErrorOnce(SiteKey, FString::Printf(TEXT("%s has no parameter %s"), *Func->GetName(), *Pin.ToString())); return nullptr; }
		return P;
	}

	void FCall::FailInput(const FString& Msg)
	{
		bInputFailed = true;
		ErrorOnce(SiteKey, Msg);
	}

	void FCall::Invoke()
	{
		// rev 5 (review 3 P1): a rejected input never becomes a call with that parameter left at its default value
		if (bInputFailed)
		{
			ErrorOnce(reinterpret_cast<const uint8*>(SiteKey) + 1, FString::Printf(TEXT("%s NOT called: input %s was rejected (see the error above); outputs keep zero values"),
				Func ? *Func->GetName() : TEXT("?"), *FirstFailedPin.ToString()));
			return;
		}
		if (Ok() && IsValid(Target)) { Target->ProcessEvent(Func, Buffer); }
	}

	// rev 4: pending Delay countdowns, keyed by (owner, node, layer epoch); the value is the world whose timer manager owns it.
	using FDelayKey = TTuple<TWeakObjectPtr<UObject>, const void*, int32>;
	static TMap<FDelayKey, TWeakObjectPtr<UWorld>> GPendingDelays;

	void Delay(UObject* Owner, const void* NodeKey, int32 LayerEpoch, float Seconds, TFunction<bool()> IsStillValid, TFunction<void()> Then)
	{
		static bool bHooked = false;
		if (!bHooked)
		{
			bHooked = true;
			// a world torn down before its timers fire never calls them: drop its entries (and any whose owner is gone)
			FWorldDelegates::OnWorldCleanup.AddLambda([](UWorld* World, bool, bool)
			{
				for (auto It = GPendingDelays.CreateIterator(); It; ++It)
				{
					if (!It->Value.IsValid() || It->Value.Get() == World || !It->Key.Get<0>().IsValid()) { It.RemoveCurrent(); }
				}
			});
		}
		UWorld* W = Owner ? Owner->GetWorld() : nullptr;
		if (!W) { return; }
		const FDelayKey Key(Owner, NodeKey, LayerEpoch);
		if (GPendingDelays.Contains(Key)) { return; }   // Blueprint Delay: ignored while counting down (same epoch)
		GPendingDelays.Add(Key, W);
		FTimerHandle H;
		W->GetTimerManager().SetTimer(H, FTimerDelegate::CreateLambda([Key, IsStillValid, Then]()
		{
			GPendingDelays.Remove(Key);
			// dropped if the HUD is gone, or its layer was switched back to Blueprint / re-enabled since (epoch changed)
			if (Key.Get<0>().IsValid() && IsStillValid && IsStillValid()) { Then(); }
		}), FMath::Max(0.0001f, Seconds), false);
	}

	AActor* BeginSpawn(UObject* WorldContext, UClass* Class, const FTransform& Transform, int64 CollisionMethod, int64 ScaleMethod, AActor* Owner, APawn* Instigator)
	{
		UWorld* W = WorldContext ? WorldContext->GetWorld() : nullptr;
		if (!W || !Class || !Class->IsChildOf(AActor::StaticClass())) { return nullptr; }
		return W->SpawnActorDeferred<AActor>(Class, Transform, Owner, Instigator, ESpawnActorCollisionHandlingMethod(CollisionMethod),
			ESpawnActorScaleMethod(ScaleMethod));
	}

	void FinishSpawn(AActor* Actor, const FTransform& Transform)
	{
		if (Actor) { Actor->FinishSpawning(Transform); }
	}

	void CallParentEvent(UObject* Self, const TCHAR* ParentClassPath, FName EventName, int32 SizeX, int32 SizeY)
	{
		if (!Self) { return; }
		struct FEntry { TWeakObjectPtr<UFunction> Fn; uint32 Epoch = 0; };
		static TMap<FString, FEntry> Cache;
		const FString Key = FString(ParentClassPath) + TEXT(":") + EventName.ToString();
		FEntry& E = Cache.FindOrAdd(Key);
		UFunction* Fn = E.Fn.Get();
		if (!Fn || E.Epoch != ReflectionEpoch())
		{
			UClass* Parent = StaticLoadClass(UObject::StaticClass(), nullptr, ParentClassPath);
			Fn = Parent ? Parent->FindFunctionByName(EventName) : nullptr;   // the parent's own (or inherited) implementation
			if (!Fn) { ErrorOnce(ParentClassPath, FString::Printf(TEXT("parent event %s not found on %s"), *EventName.ToString(), ParentClassPath)); return; }
			E.Fn = Fn;
			E.Epoch = ReflectionEpoch();
		}
		if (!Fn->Script.Num() && !Fn->HasAnyFunctionFlags(FUNC_Native)) { return; }   // engine HUD's empty implementable event: nothing to run
		uint8* Buf = static_cast<uint8*>(FMemory_Alloca(FMath::Max<int32>(1, Fn->ParmsSize)));
		FMemory::Memzero(Buf, Fn->ParmsSize);
		Fn->InitializeStruct(Buf);
		if (FIntProperty* X = CastField<FIntProperty>(Fn->FindPropertyByName(TEXT("SizeX")))) { X->SetPropertyValue_InContainer(Buf, SizeX); }
		if (FIntProperty* Y = CastField<FIntProperty>(Fn->FindPropertyByName(TEXT("SizeY")))) { Y->SetPropertyValue_InContainer(Buf, SizeY); }
		Self->ProcessEvent(Fn, Buf);
		Fn->DestroyStruct(Buf);
	}

	UObject* GetLocalPlayerSubsystem(UObject* PlayerController, UClass* SubsystemClass)
	{
		const APlayerController* PC = Cast<APlayerController>(PlayerController);
		const ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
		return (LP && SubsystemClass) ? LP->GetSubsystemBase(SubsystemClass) : nullptr;
	}
}
