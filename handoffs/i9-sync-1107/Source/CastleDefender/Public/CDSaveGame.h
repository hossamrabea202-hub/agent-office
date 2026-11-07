// #500 point 5: a versioned save game with a safe write path and a written recovery rule.
//
// File format: every slot file is an envelope: magic "CDSV", envelope format, sequence, payload length, CRC32 over the header fields AND the payload,
// then the payload (= UGameplayStatics::SaveGameToMemory bytes). Each file gets a status: Missing (no file), Unreadable (a file the platform would not
// read), Valid, Corrupt (empty, bad CRC / length / payload, or the header sequence differs from the save's own Sequence), UnsupportedFormat (an
// envelope or engine save format newer than this build), NewerVersion (valid file, SaveVersion newer than this build), ForeignSave (a well-formed
// save of another class, e.g. the game's BP_CastleSave). Old plain saves (no envelope) of UCDSaveGame are read as sequence 0.
// Payloads are never handed to UGameplayStatics::LoadGameFromMemory: it crashes the process on some corrupt files (found by the first test run).
// The CRC detects accidental damage; it is not a defence against deliberate tampering.
//
// Write (Save):
//   refuse if the slot is read-only, the incoming object is from a newer build, or ANY copy of the slot on disk is UnsupportedFormat, NewerVersion
//   or ForeignSave (never overwrite what this build cannot understand or does not own); refuse this time (not read-only) if a copy is Unreadable;
//   Migrate() the incoming object; sequence = highest existing valid sequence + 1;
//   1 write <slot>_tmp and read it back. If this fails: delete _tmp, return false, nothing committed.
//   ---- COMMIT POINT: a verified _tmp exists. Policy "a verified newer _tmp is recoverable": there is NO rollback after this point. ----
//   2 copy the current VALID main byte-for-byte to <slot>_bak and read it back. If this fails: return false, main untouched, _tmp kept.
//   3 write main and read it back. If this fails: return false, _tmp kept (main may be damaged now; _tmp and _bak still verify).
//   4 delete _tmp.
//   So Save() returning false after step 1 does NOT mean the data was discarded: the next LoadOrCreate recovers it. A crash anywhere after step 1
//   behaves exactly like an error return at the same point. A crash during step 1 leaves at worst a partial _tmp, which fails its CRC and is ignored.
//   This is not a filesystem-atomic transaction; it relies on the CRC and the read-back to tell complete copies from partial ones.
// Recovery (LoadOrCreate): among the Valid copies main, _tmp, _bak, take the highest sequence; on a tie main > _tmp > _bak. Corrupt / older copies
//   never replace a newer valid one. An UnsupportedFormat, NewerVersion or ForeignSave copy makes the slot read-only (per slot).
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
	NewerVersion,
	ForeignSave,    // a well-formed save of another class (e.g. BP_CastleSave): never overwritten
	Unreadable      // the file exists but its bytes could not be read
};

UCLASS()
class CASTLEDEFENDER_API UCDSaveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Save")
	UCDSaveGame* LoadOrCreate(const FString& Slot = TEXT("Main"));

	// True only when main holds the new data. False: refused / failed before the commit point (nothing written), or failed after it (the verified
	// _tmp is kept and the next LoadOrCreate recovers it). See the header comment.
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
