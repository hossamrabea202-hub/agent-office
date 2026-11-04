// #500 point 5: a versioned save game with a safe write path.
// - Every save carries SaveVersion; Migrate() upgrades old saves step by step (each step idempotent), so changing the game never breaks a player's save.
// - Save(): serialize + verify in memory -> write <slot>_tmp + read back -> copy the current, VALID main save byte-for-byte to <slot>_bak and verify it
//   (if that fails: stop, main untouched) -> write main + verify -> delete _tmp.
// - Load: main if valid, else _bak if valid, else a fresh save. A corrupt backup never replaces a valid main; a save from a NEWER build loads
//   read-only and is never overwritten.
// Note: SaveGameToSlot / SaveGameToMemory store every non-transient UPROPERTY of this class.
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
	UFUNCTION(BlueprintPure, Category = "Save") int32 GetInt(FName Key, int32 Fallback = 0) const { const int32* V = Ints.Find(Key); return V ? *V : Fallback; }
	UFUNCTION(BlueprintCallable, Category = "Save") void SetFloat(FName Key, float Value) { Floats.Add(Key, Value); }
	UFUNCTION(BlueprintPure, Category = "Save") float GetFloat(FName Key, float Fallback = 0.f) const { const float* V = Floats.Find(Key); return V ? *V : Fallback; }
	UFUNCTION(BlueprintCallable, Category = "Save") void SetString(FName Key, const FString& Value) { Strings.Add(Key, Value); }
	UFUNCTION(BlueprintPure, Category = "Save") FString GetString(FName Key) const { const FString* V = Strings.Find(Key); return V ? *V : FString(); }
	UFUNCTION(BlueprintCallable, Category = "Save") void SetFlag(FName Key, bool bOn) { if (bOn) { Flags.Add(Key); } else { Flags.Remove(Key); } }
	UFUNCTION(BlueprintPure, Category = "Save") bool HasFlag(FName Key) const { return Flags.Contains(Key); }

	// Upgrades an older save to CurrentVersion (safe to call again). False if the save is from a newer build.
	bool Migrate();
	bool IsNewerThanBuild() const { return SaveVersion > CurrentVersion; }
};

UCLASS()
class CASTLEDEFENDER_API UCDSaveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Save")
	UCDSaveGame* LoadOrCreate(const FString& Slot = TEXT("Main"));

	// False if anything failed; the main slot is then unchanged (or, if only the final write failed, the verified backup still holds the last good save).
	UFUNCTION(BlueprintCallable, Category = "Save")
	bool Save(UCDSaveGame* Data, const FString& Slot = TEXT("Main"));

	UFUNCTION(BlueprintPure, Category = "Save")
	UCDSaveGame* GetCurrent() const { return Current; }

	// True when the loaded save came from a newer game build: it is read-only, Save() refuses to overwrite it.
	UFUNCTION(BlueprintPure, Category = "Save")
	bool IsReadOnly() const { return bReadOnly; }

	// Test seam: reads a slot and returns it only if it deserializes into a UCDSaveGame.
	static UCDSaveGame* LoadValid(const FString& Slot);

private:
	UPROPERTY()
	TObjectPtr<UCDSaveGame> Current;

	bool bReadOnly = false;
};
