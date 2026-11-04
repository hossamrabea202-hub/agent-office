// #500 point 5: a versioned save game with a safe write path and a written recovery rule.
//
// File format: every slot file is an envelope: magic "CDSV", envelope format, sequence number, CRC32 of the payload, payload length, payload
// (= UGameplayStatics::SaveGameToMemory bytes). A file is VALID only if the magic, length and CRC match AND the payload deserializes into a
// UCDSaveGame. Old plain saves (no envelope) are still read, as sequence 0.
//
// Write (Save):
//   refuse if the slot is read-only, the incoming object is from a newer build, or ANY existing copy of the slot (main / _tmp / _bak) is newer;
//   Migrate() the incoming object first; sequence = highest existing sequence + 1;
//   write <slot>_tmp and read it back -> copy the current VALID main byte-for-byte to <slot>_bak and read it back (if that fails: stop, main untouched)
//   -> write main and read it back -> delete _tmp.
// Recovery (LoadOrCreate): among the VALID copies main, _tmp, _bak, take the highest sequence; on a tie main > _tmp > _bak.
//   _tmp only survives when a save was interrupted after its own verified write, so it is newer than main only if main never got the commit.
//   A corrupt or older copy never replaces a newer valid one. A save from a NEWER build makes that slot read-only (per slot).
// Note: SaveGameToMemory stores every non-transient UPROPERTY of UCDSaveGame.
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

	// Monotonic per slot: decides which copy is newest during recovery.
	UPROPERTY(SaveGame, BlueprintReadOnly, Category = "Save")
	int64 Sequence = 0;

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

	// Upgrades an older save to CurrentVersion (each step safe to run twice). False if the save is from a newer build (left unchanged).
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

	// False if anything failed or was refused; the main slot is then unchanged, or (if only the final write failed) the newest verified copy is in _tmp / _bak.
	UFUNCTION(BlueprintCallable, Category = "Save")
	bool Save(UCDSaveGame* Data, const FString& Slot = TEXT("Main"));

	UFUNCTION(BlueprintPure, Category = "Save")
	UCDSaveGame* GetCurrent() const { return Current; }

	// True when this slot holds a save from a newer game build: it is read-only, Save() refuses to write it. Other slots are unaffected.
	UFUNCTION(BlueprintPure, Category = "Save")
	bool IsReadOnly(const FString& Slot = TEXT("Main")) const { return ReadOnlySlots.Contains(Slot); }

	// One slot file, fully checked (envelope + CRC + deserialize). Null if missing or invalid. Public for tests.
	static UCDSaveGame* LoadValid(const FString& SlotFile);

	// Envelope helpers (public for tests).
	static void Wrap(const TArray<uint8>& Payload, int64 Sequence, TArray<uint8>& Out);
	static bool Unwrap(const TArray<uint8>& File, TArray<uint8>& OutPayload);

private:
	UPROPERTY()
	TObjectPtr<UCDSaveGame> Current;

	TSet<FString> ReadOnlySlots;
};
