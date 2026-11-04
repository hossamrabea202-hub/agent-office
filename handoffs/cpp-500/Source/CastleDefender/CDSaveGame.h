// #500 point 5: a versioned save game. Every save carries SaveVersion; Migrate() upgrades old saves step by step, so changing the game
// never breaks a player's save. Data is kept in simple named maps, so new values need no new C++ (Blueprints: SetInt / GetInt ...).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CDSaveGame.generated.h"

UCLASS(BlueprintType)
class CASTLEDEFENDER_API UCDSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	// Raise when the meaning of saved data changes, and add a step in Migrate().
	static constexpr int32 CurrentVersion = 1;

	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "Save")
	int32 SaveVersion = CurrentVersion;

	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "Save")
	FDateTime SavedAt;

	UPROPERTY(SaveGame) TMap<FName, int32> Ints;
	UPROPERTY(SaveGame) TMap<FName, float> Floats;
	UPROPERTY(SaveGame) TMap<FName, FString> Strings;
	UPROPERTY(SaveGame) TSet<FName> Flags;

	UFUNCTION(BlueprintCallable, Category = "Save") void SetInt(FName Key, int32 Value) { Ints.Add(Key, Value); }
	UFUNCTION(BlueprintPure, Category = "Save") int32 GetInt(FName Key, int32 Default = 0) const { const int32* V = Ints.Find(Key); return V ? *V : Default; }
	UFUNCTION(BlueprintCallable, Category = "Save") void SetFloat(FName Key, float Value) { Floats.Add(Key, Value); }
	UFUNCTION(BlueprintPure, Category = "Save") float GetFloat(FName Key, float Default = 0.f) const { const float* V = Floats.Find(Key); return V ? *V : Default; }
	UFUNCTION(BlueprintCallable, Category = "Save") void SetString(FName Key, const FString& Value) { Strings.Add(Key, Value); }
	UFUNCTION(BlueprintPure, Category = "Save") FString GetString(FName Key) const { const FString* V = Strings.Find(Key); return V ? *V : FString(); }
	UFUNCTION(BlueprintCallable, Category = "Save") void SetFlag(FName Key, bool bOn) { if (bOn) { Flags.Add(Key); } else { Flags.Remove(Key); } }
	UFUNCTION(BlueprintPure, Category = "Save") bool HasFlag(FName Key) const { return Flags.Contains(Key); }

	// Upgrades an older save to CurrentVersion. Returns false if the save is newer than this game build (do not overwrite it).
	bool Migrate();
};

// Save / load with a safety copy: before overwriting slot X it copies X to X_bak, so one bad save never loses the player's progress.
UCLASS()
class CASTLEDEFENDER_API UCDSaveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Save")
	UCDSaveGame* LoadOrCreate(const FString& Slot = TEXT("Main"));

	UFUNCTION(BlueprintCallable, Category = "Save")
	bool Save(UCDSaveGame* Data, const FString& Slot = TEXT("Main"));

	UFUNCTION(BlueprintPure, Category = "Save")
	UCDSaveGame* GetCurrent() const { return Current; }

private:
	UPROPERTY()
	TObjectPtr<UCDSaveGame> Current;
};
