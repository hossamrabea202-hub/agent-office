// CDHudGenRuntime.h - hand-written runtime used by the GENERATED HUD layer code (CDHudGen_*.cpp).   REVIEW DRAFT rev 5, 2026-11-06.
// rev 5 (third review): FCall records every failed input (missing parameter, type mismatch, refused object or array) and Invoke()
// then refuses the call with an Error - a rejected input never turns into a call with default values. Error sites of generated
// conversions are unique strings (CDGEN_SITE(n): file, line and a per-layer counter), deduplicated by VALUE, not pointer.
// rev 4 (second review): object-array writes validate the WHOLE array first and refuse the write on any mismatch (Error with
// property, owner class, element index, actual and expected class) instead of storing nullptr; ToTyped takes a stable call-site
// identity (CDGEN_CALLSITE = generated file and line) and reports the element index; Delay identity includes the layer epoch.
// rev 2 (ChatGPT review): no reinterpret_cast between array types (real, validated conversion); every reflected access checks the
// actual FProperty type before touching memory; property / function caches are invalidated when Blueprints are reinstanced;
// Delay continuations carry a layer epoch and are dropped when the layer was switched off (see CDHudLayers).
// Every failure logs an Error once per call site ("cd.HudGen: ...") and yields a zero value; nothing writes through a mismatched type.
#pragma once

#include "CoreMinimal.h"
#include "UObject/UnrealType.h"
#include "UObject/Class.h"
#include "InputCoreTypes.h"
#include "Engine/HitResult.h"

class UWorld;

namespace CDGen
{
	CASTLEDEFENDER_API UObject* LoadAssetByPath(const TCHAR* Path);
	CASTLEDEFENDER_API UClass* LoadClassByPath(const TCHAR* Path);
	CASTLEDEFENDER_API int64 EnumValue(const TCHAR* EnumPath, const TCHAR* ValueName);
	CASTLEDEFENDER_API void ErrorOnce(const void* Site, const FString& Msg);

	// Incremented whenever objects are reinstanced (Blueprint recompile in the editor): every cached FProperty / UFunction is
	// looked up again on its next use. (A recompile may keep the UClass pointer but destroy and recreate its properties.)
	CASTLEDEFENDER_API uint32 ReflectionEpoch();

	// ---------- constants: one load per call site ----------
#define CDGEN_ASSET(Type, Path) ([]() -> Type* { static TWeakObjectPtr<UObject> P; if (!P.IsValid()) { P = CDGen::LoadAssetByPath(TEXT(Path)); } return Cast<Type>(P.Get()); }())
#define CDGEN_CLASS(Path)       ([]() -> UClass* { static TWeakObjectPtr<UClass> P; if (!P.IsValid()) { P = CDGen::LoadClassByPath(TEXT(Path)); } return P.Get(); }())
#define CDGEN_NAME(Str)         ([]() -> const FName& { static const FName N(TEXT(Str)); return N; }())
	// rev 4: stable diagnostic identity of a generated call site: "<generated file>(<line>)". One literal per site, so ErrorOnce
	// keys never collide (a function argument's address is not a site identity) and the message says where to look.
#define CDGEN_STR2(x) #x
#define CDGEN_STR(x) CDGEN_STR2(x)
#define CDGEN_CALLSITE TEXT(__FILE__ "(" CDGEN_STR(__LINE__) ")")
	// rev 5 (review 3 P2): the generator numbers every conversion site of a layer, so two sites never share a string even on one
	// line, and ErrorOnceText deduplicates by the string's VALUE (immune to literal pooling).
#define CDGEN_SITE(N) TEXT(__FILE__ "(" CDGEN_STR(__LINE__) ")#" #N)
	CASTLEDEFENDER_API void ErrorOnceText(const TCHAR* Site, const FString& Msg);

	// rev 4: every element of an object array must be null or an instance of Expected. On the first bad element: Error (once per
	// site) naming what, the element index, its class and the expected class; returns false and the caller writes NOTHING.
	template <typename E> bool ValidateObjectArray(const void* Site, const TCHAR* What, const TArray<E>& V, const UClass* Expected)
	{
		for (int32 i = 0; i < V.Num(); ++i)
		{
			const UObject* O = static_cast<const UObject*>(V[i]);
			if (O && !O->IsA(Expected))
			{
				ErrorOnce(Site, FString::Printf(TEXT("%s: element [%d] is a %s, expected %s - write refused, destination unchanged"),
					What, i, *O->GetClass()->GetName(), *Expected->GetName()));
				return false;
			}
		}
		return true;
	}
#define CDGEN_KEY(Str)          ([]() -> const FKey& { static const FKey K(TEXT(Str)); return K; }())
#define CDGEN_ENUM(Path, Name)  ([]() -> int64 { static const int64 V = CDGen::EnumValue(TEXT(Path), TEXT(Name)); return V; }())

	// ---------- type checks: does this FProperty really hold a T? ----------
	template <typename T> struct TIsArray { static constexpr bool Value = false; };
	template <typename E> struct TIsArray<TArray<E>> { static constexpr bool Value = true; using Elem = E; };
	// object-pointer arrays get their own trait so "is it an object array" never names Elem of a non-array type
	template <typename T> struct TIsObjArray { static constexpr bool Value = false; };
	template <typename E> struct TIsObjArray<TArray<E*>> { static constexpr bool Value = true; using Elem = E*; };

	template <typename T> UScriptStruct* StructOf()
	{
		if constexpr (std::is_same_v<T, FKey>) { return FKey::StaticStruct(); }
		else if constexpr (std::is_same_v<T, FHitResult>) { return FHitResult::StaticStruct(); }
		else { return TBaseStructure<T>::Get(); }   // FVector, FVector2D, FRotator, FLinearColor, FColor, FTransform
	}

	template <typename T> bool Matches(const FProperty* P)
	{
		if (!P) { return false; }
		if constexpr (std::is_same_v<T, bool>) { return P->IsA<FBoolProperty>(); }
		else if constexpr (std::is_same_v<T, int32>) { return P->IsA<FIntProperty>(); }
		else if constexpr (std::is_same_v<T, int64>) { return P->IsA<FInt64Property>(); }
		else if constexpr (std::is_same_v<T, uint8>)
		{
			if (P->IsA<FByteProperty>()) { return true; }
			const FEnumProperty* E = CastField<FEnumProperty>(P);
			return E && E->GetUnderlyingProperty() && E->GetUnderlyingProperty()->GetElementSize() == 1;
		}
		else if constexpr (std::is_same_v<T, float> || std::is_same_v<T, double>) { return P->IsA<FFloatProperty>() || P->IsA<FDoubleProperty>(); }
		else if constexpr (std::is_same_v<T, FString>) { return P->IsA<FStrProperty>(); }
		else if constexpr (std::is_same_v<T, FName>) { return P->IsA<FNameProperty>(); }
		else if constexpr (std::is_same_v<T, FText>) { return P->IsA<FTextProperty>(); }
		else if constexpr (std::is_pointer_v<T>)
		{
			const FObjectPropertyBase* O = CastField<FObjectPropertyBase>(P);
			return O && !P->IsA<FWeakObjectProperty>() && !P->IsA<FSoftObjectProperty>() && !P->IsA<FLazyObjectProperty>();   // raw / TObjectPtr only
		}
		else if constexpr (TIsArray<T>::Value)
		{
			const FArrayProperty* A = CastField<FArrayProperty>(P);
			return A && Matches<typename TIsArray<T>::Elem>(A->Inner);
		}
		else
		{
			const FStructProperty* S = CastField<FStructProperty>(P);
			return S && S->Struct == StructOf<T>();
		}
	}

	CASTLEDEFENDER_API FString DescribeMismatch(const FProperty* P, const TCHAR* Wanted);

	// ---------- Blueprint / native member variables by reflection ----------
	struct FPropSite { const UClass* Class = nullptr; uint32 Epoch = 0; FProperty* Prop = nullptr; };
	CASTLEDEFENDER_API FProperty* FindProp(FPropSite& Site, const UObject* Obj, FName Name);

	template <typename T> T GetVar(const UObject* Obj, FName Name, FPropSite& Site)
	{
		FProperty* P = Obj ? FindProp(Site, Obj, Name) : nullptr;
		if (!P) { return T{}; }
		if (!Matches<T>(P)) { ErrorOnce(&Site, DescribeMismatch(P, *Name.ToString())); return T{}; }
		const void* Ptr = P->ContainerPtrToValuePtr<void>(Obj);
		if constexpr (std::is_same_v<T, bool>) { return CastFieldChecked<FBoolProperty>(P)->GetPropertyValue(Ptr); }
		else if constexpr (std::is_pointer_v<T>) { return Cast<std::remove_pointer_t<T>>(CastFieldChecked<FObjectPropertyBase>(P)->GetObjectPropertyValue(Ptr)); }
		else if constexpr (std::is_same_v<T, double> || std::is_same_v<T, float>)
		{
			if (const FDoubleProperty* D = CastField<FDoubleProperty>(P)) { return T(D->GetPropertyValue(Ptr)); }
			return T(CastFieldChecked<FFloatProperty>(P)->GetPropertyValue(Ptr));
		}
		else if constexpr (std::is_same_v<T, uint8>)
		{
			if (const FEnumProperty* E = CastField<FEnumProperty>(P)) { return uint8(E->GetUnderlyingProperty()->GetUnsignedIntPropertyValue(Ptr)); }
			return CastFieldChecked<FByteProperty>(P)->GetPropertyValue(Ptr);
		}
		else if constexpr (TIsObjArray<T>::Value)
		{
			// object arrays: element by element through the inner property (TObjectPtr storage safe), validated by Cast
			T Out;
			const FArrayProperty* A = CastFieldChecked<FArrayProperty>(P);
			FScriptArrayHelper H(A, Ptr);
			const FObjectPropertyBase* In = CastFieldChecked<FObjectPropertyBase>(A->Inner);
			Out.Reserve(H.Num());
			for (int32 i = 0; i < H.Num(); ++i) { Out.Add(Cast<std::remove_pointer_t<typename TIsObjArray<T>::Elem>>(In->GetObjectPropertyValue(H.GetRawPtr(i)))); }
			return Out;
		}
		else { return *static_cast<const T*>(Ptr); }   // type proven by Matches<T>: same C++ layout
	}

	template <typename T> void SetVar(UObject* Obj, FName Name, FPropSite& Site, const T& Value)
	{
		FProperty* P = Obj ? FindProp(Site, Obj, Name) : nullptr;
		if (!P) { return; }
		if (!Matches<T>(P)) { ErrorOnce(&Site, DescribeMismatch(P, *Name.ToString())); return; }
		void* Ptr = P->ContainerPtrToValuePtr<void>(Obj);
		if constexpr (std::is_same_v<T, bool>) { CastFieldChecked<FBoolProperty>(P)->SetPropertyValue(Ptr, Value); }
		else if constexpr (std::is_pointer_v<T>)
		{
			const FObjectPropertyBase* O = CastFieldChecked<FObjectPropertyBase>(P);
			UObject* V = const_cast<UObject*>(static_cast<const UObject*>(Value));
			if (V && !V->IsA(O->PropertyClass)) { ErrorOnce(&Site, FString::Printf(TEXT("%s: refusing %s (not a %s)"), *Name.ToString(), *V->GetClass()->GetName(), *O->PropertyClass->GetName())); return; }
			O->SetObjectPropertyValue(Ptr, V);
		}
		else if constexpr (std::is_same_v<T, double> || std::is_same_v<T, float>)
		{
			if (FDoubleProperty* D = CastField<FDoubleProperty>(P)) { D->SetPropertyValue(Ptr, double(Value)); }
			else { CastFieldChecked<FFloatProperty>(P)->SetPropertyValue(Ptr, float(Value)); }
		}
		else if constexpr (std::is_same_v<T, uint8>)
		{
			if (FEnumProperty* E = CastField<FEnumProperty>(P)) { E->GetUnderlyingProperty()->SetIntPropertyValue(Ptr, uint64(Value)); }
			else { CastFieldChecked<FByteProperty>(P)->SetPropertyValue(Ptr, Value); }
		}
		else if constexpr (TIsObjArray<T>::Value)
		{
			const FArrayProperty* A = CastFieldChecked<FArrayProperty>(P);
			const FObjectPropertyBase* In = CastFieldChecked<FObjectPropertyBase>(A->Inner);
			// rev 4: validate everything before the destination is touched; a mismatch is an Error and the array stays as it was
			const FString What = FString::Printf(TEXT("%s.%s"), *Obj->GetClass()->GetName(), *Name.ToString());
			if (!ValidateObjectArray(&Site, *What, Value, In->PropertyClass)) { return; }
			FScriptArrayHelper H(A, Ptr);
			H.Resize(Value.Num());
			for (int32 i = 0; i < Value.Num(); ++i) { In->SetObjectPropertyValue(H.GetRawPtr(i), const_cast<UObject*>(static_cast<const UObject*>(Value[i]))); }
		}
		else { *static_cast<T*>(Ptr) = Value; }
	}

	// Pointer to a container property for in-place Array_Add / RemoveItem / Remove / Clear (Blueprint by-ref arrays).
	// Only for non-object element types (object arrays go through GetVar/SetVar so TObjectPtr storage is respected).
	template <typename T> T* VarRef(UObject* Obj, FName Name, FPropSite& Site)
	{
		static_assert(TIsArray<T>::Value && !TIsObjArray<T>::Value, "object arrays: use GetVar + SetVar");
		FProperty* P = Obj ? FindProp(Site, Obj, Name) : nullptr;
		if (!P) { return nullptr; }
		if (!Matches<T>(P)) { ErrorOnce(&Site, DescribeMismatch(P, *Name.ToString())); return nullptr; }
		return P->ContainerPtrToValuePtr<T>(Obj);
	}

	// ---------- typed object arrays: real conversion, no reinterpret_cast ----------
	// Generic object arrays are TArray<UObject*>. A native function taking TArray<AActor*> gets a converted copy; an element that
	// is not an AActor becomes nullptr and is reported (the index layout is kept, as Blueprint keeps it).
	// rev 4: Site is the generated call site (CDGEN_CALLSITE), the error names it and the element index.
	template <typename To> TArray<To*> ToTyped(const TArray<UObject*>& In, const TCHAR* Site)
	{
		TArray<To*> Out;
		Out.Reserve(In.Num());
		for (int32 i = 0; i < In.Num(); ++i)
		{
			UObject* O = In[i];
			To* T = Cast<To>(O);
			if (O && !T) { ErrorOnceText(Site, FString::Printf(TEXT("%s: array element [%d] %s (%s) is not a %s - passed as null, as Blueprint does"), Site, i, *O->GetName(), *O->GetClass()->GetName(), *To::StaticClass()->GetName())); }
			Out.Add(T);
		}
		return Out;
	}
	template <typename From> TArray<UObject*> ToObjects(const TArray<From*>& In)
	{
		TArray<UObject*> Out;
		Out.Reserve(In.Num());
		for (From* F : In) { Out.Add(F); }
		return Out;
	}

	// ---------- generic reflection call ----------
	struct FFuncSite { const UClass* Class = nullptr; uint32 Epoch = 0; UFunction* Func = nullptr; };
	class CASTLEDEFENDER_API FCall
	{
	public:
		// Static functions: pass the owning class path; member functions: pass the target object.
		FCall(FFuncSite& Site, UObject* Target, FName FuncName, const TCHAR* OwnerClassPath);
		~FCall();
		bool Ok() const { return Func != nullptr && Target != nullptr; }
		// rev 5: true once any Set() was rejected; Invoke() then does not call the function
		bool HasInputError() const { return bInputFailed; }
		template <typename T> void Set(FName Pin, const T& V);
		template <typename T> T Get(FName Pin) const;
		void Invoke();
	private:
		FProperty* Param(FName Pin) const;
		void FailInput(const FString& Msg);   // rev 5: Error once per site + mark the call
		bool bInputFailed = false;
		FName FirstFailedPin;
		UObject* Target = nullptr;
		UFunction* Func = nullptr;
		uint8* Buffer = nullptr;
		const void* SiteKey = nullptr;
	};

	// ---------- Delay emulation ----------
	// Blueprint Delay: starts a countdown; while it is pending, further executions of the same Delay node are ignored.
	// rev 2: Then runs only if IsStillValid() is true when the timer fires (the layer is still native and in the same epoch).
	// rev 4: the pending identity is (owner, node, layer epoch), so a countdown left over from an earlier native epoch never blocks
	// the same Delay after the layer was switched away and back; it fires later, finds its epoch stale and only removes itself.
	// Entries of a world that is cleaned up before its timers fire are dropped (FWorldDelegates::OnWorldCleanup).
	CASTLEDEFENDER_API void Delay(UObject* Owner, const void* NodeKey, int32 LayerEpoch, float Seconds, TFunction<bool()> IsStillValid, TFunction<void()> Then);

	// Spawn Actor From Class: deferred spawn so exposed-on-spawn pins can be written first (same order as the K2 node).
	CASTLEDEFENDER_API AActor* BeginSpawn(UObject* WorldContext, UClass* Class, const FTransform& Transform, int64 CollisionMethod, int64 ScaleMethod, AActor* Owner, APawn* Instigator);
	CASTLEDEFENDER_API void FinishSpawn(AActor* Actor, const FTransform& Transform);

	// "Parent: <Event>" node: runs the PARENT class's implementation of the event on Self, directly (no virtual dispatch,
	// so it never re-enters the calling level). Parameters: the draw event's SizeX / SizeY.
	CASTLEDEFENDER_API void CallParentEvent(UObject* Self, const TCHAR* ParentClassPath, FName EventName, int32 SizeX, int32 SizeY);

	// Get Subsystem (Local Player) from a player controller.
	CASTLEDEFENDER_API UObject* GetLocalPlayerSubsystem(UObject* PlayerController, UClass* SubsystemClass);

	// ---------- FCall typed Set / Get (types checked against the real parameter) ----------
	template <typename T> void FCall::Set(FName Pin, const T& V)
	{
		FProperty* P = Param(Pin);
		if (!P) { if (Func) { FirstFailedPin = FirstFailedPin.IsNone() ? Pin : FirstFailedPin; bInputFailed = true; } return; }   // Param logged it
		void* Dst = P->ContainerPtrToValuePtr<void>(Buffer);
		if constexpr (std::is_same_v<T, int64>)   // enums / bytes / ints passed as int64
		{
			if (FByteProperty* By = CastField<FByteProperty>(P)) { By->SetPropertyValue(Dst, uint8(V)); }
			else if (FEnumProperty* E = CastField<FEnumProperty>(P)) { E->GetUnderlyingProperty()->SetIntPropertyValue(Dst, V); }
			else if (FNumericProperty* N = CastField<FNumericProperty>(P); N && N->IsInteger()) { N->SetIntPropertyValue(Dst, V); }
			else { FirstFailedPin = Pin; FailInput(DescribeMismatch(P, TEXT("integer/enum parameter"))); }
		}
		else if (!Matches<T>(P)) { FirstFailedPin = Pin; FailInput(DescribeMismatch(P, *Pin.ToString())); }
		else if constexpr (std::is_same_v<T, bool>) { CastFieldChecked<FBoolProperty>(P)->SetPropertyValue(Dst, V); }
		else if constexpr (std::is_pointer_v<T>)
		{
			const FObjectPropertyBase* O = CastFieldChecked<FObjectPropertyBase>(P);
			UObject* Obj = const_cast<UObject*>(static_cast<const UObject*>(V));
			if (Obj && !Obj->IsA(O->PropertyClass)) { FirstFailedPin = Pin; FailInput(FString::Printf(TEXT("%s(%s): refusing %s (not a %s)"), *Func->GetName(), *Pin.ToString(), *Obj->GetClass()->GetName(), *O->PropertyClass->GetName())); }
			else { O->SetObjectPropertyValue(Dst, Obj); }
		}
		else if constexpr (std::is_same_v<T, double> || std::is_same_v<T, float>)
		{
			if (FDoubleProperty* D = CastField<FDoubleProperty>(P)) { D->SetPropertyValue(Dst, double(V)); }
			else { CastFieldChecked<FFloatProperty>(P)->SetPropertyValue(Dst, float(V)); }
		}
		else if constexpr (std::is_same_v<T, uint8>) { CastFieldChecked<FByteProperty>(P)->SetPropertyValue(Dst, V); }
		else if constexpr (TIsObjArray<T>::Value)
		{
			const FArrayProperty* A = CastFieldChecked<FArrayProperty>(P);
			const FObjectPropertyBase* In = CastFieldChecked<FObjectPropertyBase>(A->Inner);
			// rev 4: same whole-array validation as SetVar (a native function's parameter must not receive a wrong-class object)
			const FString What = FString::Printf(TEXT("%s(%s)"), *Func->GetName(), *Pin.ToString());
			if (!ValidateObjectArray(SiteKey, *What, V, In->PropertyClass)) { FirstFailedPin = Pin; bInputFailed = true; return; }   // logged by the validator
			FScriptArrayHelper H(A, Dst);
			H.Resize(V.Num());
			for (int32 i = 0; i < V.Num(); ++i) { In->SetObjectPropertyValue(H.GetRawPtr(i), const_cast<UObject*>(static_cast<const UObject*>(V[i]))); }
		}
		else { *static_cast<T*>(Dst) = V; }
	}
	template <typename T> T FCall::Get(FName Pin) const
	{
		FProperty* P = Param(Pin);
		if (!P) { return T{}; }
		if (!Matches<T>(P)) { ErrorOnce(SiteKey, DescribeMismatch(P, *Pin.ToString())); return T{}; }
		const void* Src = P->ContainerPtrToValuePtr<void>(Buffer);
		if constexpr (std::is_same_v<T, bool>) { return CastFieldChecked<FBoolProperty>(P)->GetPropertyValue(Src); }
		else if constexpr (std::is_pointer_v<T>) { return Cast<std::remove_pointer_t<T>>(CastFieldChecked<FObjectPropertyBase>(P)->GetObjectPropertyValue(Src)); }
		else if constexpr (std::is_same_v<T, double> || std::is_same_v<T, float>)
		{
			if (const FDoubleProperty* D = CastField<FDoubleProperty>(P)) { return T(D->GetPropertyValue(Src)); }
			return T(CastFieldChecked<FFloatProperty>(P)->GetPropertyValue(Src));
		}
		else if constexpr (std::is_same_v<T, uint8>) { return CastFieldChecked<FByteProperty>(P)->GetPropertyValue(Src); }
		else if constexpr (TIsObjArray<T>::Value)
		{
			T Out;
			const FArrayProperty* A = CastFieldChecked<FArrayProperty>(P);
			const FObjectPropertyBase* In = CastFieldChecked<FObjectPropertyBase>(A->Inner);
			FScriptArrayHelper H(A, Src);
			for (int32 i = 0; i < H.Num(); ++i) { Out.Add(Cast<std::remove_pointer_t<typename TIsObjArray<T>::Elem>>(In->GetObjectPropertyValue(H.GetRawPtr(i)))); }
			return Out;
		}
		else { return *static_cast<const T*>(Src); }
	}
}
