#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Crc.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"

namespace
{
	const uint32 EnvelopeMagic = 0x56534443;   // "CDSV" little-endian
	const uint32 EnvelopeFormat = 1;
	const int32 HeaderSize = 4 + 4 + 8 + 4 + 4;

	bool ReadBytes(const FString& SlotFile, TArray<uint8>& Out)
	{
		Out.Reset();
		return UGameplayStatics::DoesSaveGameExist(SlotFile, 0) && UGameplayStatics::LoadDataFromSlot(Out, SlotFile, 0) && Out.Num() > 0;
	}

	bool WriteVerified(const TArray<uint8>& Bytes, const FString& SlotFile)
	{
		TArray<uint8> Back;
		return UGameplayStatics::SaveDataToSlot(Bytes, SlotFile, 0) && ReadBytes(SlotFile, Back) && Back == Bytes;
	}

	// The three files of one slot, in tie-break order.
	TArray<FString, TInlineAllocator<3>> SlotFiles(const FString& Slot)
	{
		return { Slot, Slot + TEXT("_tmp"), Slot + TEXT("_bak") };
	}
}

bool UCDSaveGame::Migrate()
{
	if (IsNewerThanBuild())
	{
		return false;
	}
	// One step per version bump, oldest first; each step must be safe to run twice. Example for a future version 2:
	// if (SaveVersion < 2) { Ints.FindOrAdd(TEXT("Gems")); SaveVersion = 2; }
	SaveVersion = CurrentVersion;
	return true;
}

void UCDSaveSubsystem::Wrap(const TArray<uint8>& Payload, int64 Sequence, TArray<uint8>& Out)
{
	Out.Reset(HeaderSize + Payload.Num());
	FMemoryWriter W(Out);
	uint32 Magic = EnvelopeMagic, Format = EnvelopeFormat, Crc = FCrc::MemCrc32(Payload.GetData(), Payload.Num()), Len = Payload.Num();
	W << Magic << Format << Sequence << Crc << Len;
	Out.Append(Payload);
}

bool UCDSaveSubsystem::Unwrap(const TArray<uint8>& File, TArray<uint8>& OutPayload)
{
	OutPayload.Reset();
	if (File.Num() >= HeaderSize)
	{
		FMemoryReader R(File);
		uint32 Magic = 0, Format = 0, Crc = 0, Len = 0;
		int64 Sequence = 0;
		R << Magic;
		if (Magic == EnvelopeMagic)
		{
			R << Format << Sequence << Crc << Len;
			if (Format != EnvelopeFormat || (int64)Len != (int64)File.Num() - HeaderSize)
			{
				return false;
			}
			OutPayload.Append(File.GetData() + HeaderSize, Len);
			return FCrc::MemCrc32(OutPayload.GetData(), OutPayload.Num()) == Crc;
		}
	}
	OutPayload = File;   // legacy plain save (no envelope): validity is decided by deserializing
	return File.Num() > 0;
}

UCDSaveGame* UCDSaveSubsystem::LoadValid(const FString& SlotFile)
{
	TArray<uint8> File, Payload;
	if (!ReadBytes(SlotFile, File) || !Unwrap(File, Payload))
	{
		return nullptr;
	}
	return Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromMemory(Payload));
}

UCDSaveGame* UCDSaveSubsystem::LoadOrCreate(const FString& Slot)
{
	ReadOnlySlots.Remove(Slot);
	UCDSaveGame* Best = nullptr;
	FString BestFile;
	bool bAnyNewer = false;
	for (const FString& File : SlotFiles(Slot))
	{
		UCDSaveGame* Copy = LoadValid(File);
		if (!Copy)
		{
			if (UGameplayStatics::DoesSaveGameExist(File, 0))
			{
				UE_LOG(LogTemp, Warning, TEXT("CDSave: %s is not valid (checksum or format); ignored, left on disk"), *File);
			}
			continue;
		}
		bAnyNewer |= Copy->IsNewerThanBuild();
		if (!Best || Copy->Sequence > Best->Sequence)   // strict >: on a tie the earlier file (main > _tmp > _bak) wins
		{
			Best = Copy;
			BestFile = File;
		}
	}
	if (bAnyNewer)
	{
		ReadOnlySlots.Add(Slot);
		UE_LOG(LogTemp, Error, TEXT("CDSave: slot %s holds a save from a newer build: loaded read-only"), *Slot);
	}
	if (Best && !bAnyNewer)
	{
		if (BestFile != Slot)
		{
			UE_LOG(LogTemp, Warning, TEXT("CDSave: recovered slot %s from %s (sequence %lld)"), *Slot, *BestFile, Best->Sequence);
		}
		Best->Migrate();
	}
	if (!Best)
	{
		Best = Cast<UCDSaveGame>(UGameplayStatics::CreateSaveGameObject(UCDSaveGame::StaticClass()));
	}
	Current = Best;
	return Best;
}

bool UCDSaveSubsystem::Save(UCDSaveGame* Data, const FString& Slot)
{
	if (!Data)
	{
		return false;
	}
	if (ReadOnlySlots.Contains(Slot) || Data->IsNewerThanBuild())
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: refusing to write %s: read-only or data from a newer build"), *Slot);
		return false;
	}
	// Look at what is on disk now, whatever this session loaded: never overwrite a newer build's save; continue the sequence.
	int64 MaxSequence = 0;
	for (const FString& File : SlotFiles(Slot))
	{
		if (const UCDSaveGame* Existing = LoadValid(File))
		{
			if (Existing->IsNewerThanBuild())
			{
				ReadOnlySlots.Add(Slot);
				UE_LOG(LogTemp, Error, TEXT("CDSave: %s on disk is from a newer build (version %d); refusing to overwrite"), *File, Existing->SaveVersion);
				return false;
			}
			MaxSequence = FMath::Max(MaxSequence, Existing->Sequence);
		}
	}
	if (!Data->Migrate())
	{
		return false;
	}
	Data->Sequence = MaxSequence + 1;
	Data->SavedAt = FDateTime::UtcNow();

	// 1. serialize, check it reads back as a save, wrap with checksum
	TArray<uint8> Payload, File;
	if (!UGameplayStatics::SaveGameToMemory(Data, Payload) || !Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromMemory(Payload)))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: %s did not serialize cleanly; nothing written"), *Slot);
		return false;
	}
	Wrap(Payload, Data->Sequence, File);
	// 2. temp copy, read back
	const FString Tmp = Slot + TEXT("_tmp");
	if (!WriteVerified(File, Tmp))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: could not write %s; main untouched"), *Tmp);
		return false;
	}
	// 3. back up the current main byte-for-byte, only if it is valid (a corrupt main never replaces a good backup)
	TArray<uint8> Old;
	if (ReadBytes(Slot, Old))
	{
		if (LoadValid(Slot))
		{
			if (!WriteVerified(Old, Slot + TEXT("_bak")))
			{
				UE_LOG(LogTemp, Error, TEXT("CDSave: backup of %s failed; main untouched, the new save stays in %s"), *Slot, *Tmp);
				return false;
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("CDSave: %s was not valid; keeping the existing %s_bak"), *Slot, *Slot);
		}
	}
	// 4. main
	if (!WriteVerified(File, Slot))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: writing %s failed; recovery will use %s (sequence %lld)"), *Slot, *Tmp, Data->Sequence);
		return false;
	}
	UGameplayStatics::DeleteGameInSlot(Tmp, 0);
	Current = Data;
	return true;
}
