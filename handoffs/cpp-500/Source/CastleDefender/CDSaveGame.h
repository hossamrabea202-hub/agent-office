// #500 point 5: a versioned save game with a safe write path and a written recovery rule.
//
// File format: every slot file is an envelope: magic "CDSV", envelope format, sequence, payload length, CRC32 over the header fields AND the payload,
// then the payload (= UGameplayStatics::SaveGameToMemory bytes). Each file gets a status: Missing, Valid, Corrupt (bad CRC / length / payload, or the
// header sequence differs from the save's own Sequence), UnsupportedFormat (an envelope format newer than this build), NewerVersion (valid file,
// SaveVersion newer than this build). Old plain saves (no envelope) are read as sequence 0.
//
// Write (Save):
//   refuse if the slot is read-only, the incoming object is from a newer build, or ANY copy of the slot on disk is UnsupportedFormat or NewerVersion
//   (an older build never overwrites what it cannot understand); Migrate() the incoming object; sequence = highest existing valid sequence + 1;
//   1 write <slot>_tmp and read it back
//   2 copy the current VALID main byte-for-byte to <slot>_bak and read it back. If this fails: DELETE _tmp and return false = ROLLBACK, nothing committed,
//     main untouched (a failed save is never recovered later)
//   3 write main and read it back. If this fails: return false, but the verified _tmp is KEPT as recoverable progress (main may be damaged now)
//   4 delete _tmp.
// Recovery (LoadOrCreate): among the Valid copies main, _tmp, _bak, take the highest sequence; on a tie main > _tmp > _bak. A _tmp can only be left
//   by step 3 failing (or a crash between 3 and 4), so it is newer than main only when its commit did not complete. Corrupt / older copies never
//   replace a newer valid one. An UnsupportedFormat or NewerVersion copy makes the slot read-only (per slot).
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

UENUM(BlueprintType)
enum class ECDSaveFileStatus : uint8
{
	Missing,
	Valid,
	Corrupt,
	UnsupportedFormat,
	NewerVersion
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

	// One slot file, fully checked. OutData is set only for Valid and NewerVersion. Public for tests.
	static ECDSaveFileStatus Inspect(const FString& SlotFile, UCDSaveGame*& OutData);

	// Convenience: the save object if the file is Valid (or NewerVersion), else null.
	static UCDSaveGame* LoadValid(const FString& SlotFile);

	// Envelope helpers (public for tests).
	static void Wrap(const TArray<uint8>& Payload, int64 Sequence, TArray<uint8>& Out);
	static ECDSaveFileStatus Unwrap(const TArray<uint8>& File, TArray<uint8>& OutPayload, int64& OutHeaderSequence, bool& bOutLegacy);

private:
	UPROPERTY()
	TObjectPtr<UCDSaveGame> Current;

	TSet<FString> ReadOnlySlots;
};
