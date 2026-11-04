#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Crc.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"

namespace
{
	const uint32 EnvelopeMagic = 0x56534443;   // "CDSV" little-endian
	const uint32 EnvelopeFormat = 2;           // 2 = CRC over header fields + payload (format 1 was never shipped)
	const int32 HeaderFieldsSize = 4 + 4 + 8 + 4;  // magic, format, sequence, length
	const int32 HeaderSize = HeaderFieldsSize + 4;  // + CRC

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

	uint32 EnvelopeCrc(const uint8* HeaderFields, const uint8* Payload, int32 PayloadLen)
	{
		return FCrc::MemCrc32(Payload, PayloadLen, FCrc::MemCrc32(HeaderFields, HeaderFieldsSize));
	}

	// The three files of one slot, in tie-break order.
	TArray<FString, TInlineAllocator<3>> SlotFiles(const FString& Slot)
	{
		return { Slot, Slot + TEXT("_tmp"), Slot + TEXT("_bak") };
	}

	bool Blocks(ECDSaveFileStatus S) { return S == ECDSaveFileStatus::UnsupportedFormat || S == ECDSaveFileStatus::NewerVersion; }
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
	uint32 Magic = EnvelopeMagic, Format = EnvelopeFormat, Len = Payload.Num();
	W << Magic << Format << Sequence << Len;
	uint32 Crc = EnvelopeCrc(Out.GetData(), Payload.GetData(), Payload.Num());
	W << Crc;
	Out.Append(Payload);
}

ECDSaveFileStatus UCDSaveSubsystem::Unwrap(const TArray<uint8>& File, TArray<uint8>& OutPayload, int64& OutHeaderSequence, bool& bOutLegacy)
{
	OutPayload.Reset();
	OutHeaderSequence = 0;
	bOutLegacy = false;
	if (File.Num() == 0)
	{
		return ECDSaveFileStatus::Missing;
	}
	uint32 Magic = 0;
	if (File.Num() >= 4)
	{
		FMemoryReader Peek(File);
		Peek << Magic;
	}
	if (Magic != EnvelopeMagic)
	{
		bOutLegacy = true;          // plain save from before the envelope: validity is decided by deserializing
		OutPayload = File;
		return ECDSaveFileStatus::Valid;
	}
	if (File.Num() < HeaderSize)
	{
		return ECDSaveFileStatus::Corrupt;
	}
	FMemoryReader R(File);
	uint32 Format = 0, Len = 0, Crc = 0;
	R << Magic << Format;
	if (Format > EnvelopeFormat)
	{
		return ECDSaveFileStatus::UnsupportedFormat;   // written by a newer build: protect it, never overwrite
	}
	if (Format != EnvelopeFormat)
	{
		return ECDSaveFileStatus::Corrupt;
	}
	R << OutHeaderSequence << Len << Crc;
	if ((int64)Len != (int64)File.Num() - HeaderSize || EnvelopeCrc(File.GetData(), File.GetData() + HeaderSize, Len) != Crc)
	{
		return ECDSaveFileStatus::Corrupt;
	}
	OutPayload.Append(File.GetData() + HeaderSize, Len);
	return ECDSaveFileStatus::Valid;
}

ECDSaveFileStatus UCDSaveSubsystem::Inspect(const FString& SlotFile, UCDSaveGame*& OutData)
{
	OutData = nullptr;
	TArray<uint8> File, Payload;
	if (!ReadBytes(SlotFile, File))
	{
		return ECDSaveFileStatus::Missing;
	}
	int64 HeaderSequence = 0;
	bool bLegacy = false;
	const ECDSaveFileStatus Envelope = Unwrap(File, Payload, HeaderSequence, bLegacy);
	if (Envelope != ECDSaveFileStatus::Valid)
	{
		return Envelope;
	}
	UCDSaveGame* Data = Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromMemory(Payload));
	if (!Data || (!bLegacy && Data->Sequence != HeaderSequence))
	{
		return ECDSaveFileStatus::Corrupt;   // does not deserialize, or the header and the save disagree on the sequence
	}
	OutData = Data;
	return Data->IsNewerThanBuild() ? ECDSaveFileStatus::NewerVersion : ECDSaveFileStatus::Valid;
}

UCDSaveGame* UCDSaveSubsystem::LoadValid(const FString& SlotFile)
{
	UCDSaveGame* Data = nullptr;
	Inspect(SlotFile, Data);
	return Data;
}

UCDSaveGame* UCDSaveSubsystem::LoadOrCreate(const FString& Slot)
{
	ReadOnlySlots.Remove(Slot);
	UCDSaveGame* Best = nullptr;
	FString BestFile;
	bool bBlocked = false;
	for (const FString& File : SlotFiles(Slot))
	{
		UCDSaveGame* Copy = nullptr;
		const ECDSaveFileStatus Status = Inspect(File, Copy);
		if (Blocks(Status))
		{
			bBlocked = true;
		}
		if (Status == ECDSaveFileStatus::Corrupt)
		{
			UE_LOG(LogTemp, Warning, TEXT("CDSave: %s is corrupt; ignored, left on disk"), *File);
		}
		if (!Copy)
		{
			continue;
		}
		if (!Best || Copy->Sequence > Best->Sequence)   // strict >: on a tie the earlier file (main > _tmp > _bak) wins
		{
			Best = Copy;
			BestFile = File;
		}
	}
	if (bBlocked)
	{
		ReadOnlySlots.Add(Slot);
		UE_LOG(LogTemp, Error, TEXT("CDSave: slot %s holds a save this build cannot write safely (newer format or version): read-only"), *Slot);
	}
	else if (Best)
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
	// Look at what is on disk now, whatever this session loaded: never overwrite what this build cannot understand; continue the sequence.
	int64 MaxSequence = 0;
	for (const FString& File : SlotFiles(Slot))
	{
		UCDSaveGame* Existing = nullptr;
		const ECDSaveFileStatus Status = Inspect(File, Existing);
		if (Blocks(Status))
		{
			ReadOnlySlots.Add(Slot);
			UE_LOG(LogTemp, Error, TEXT("CDSave: %s is from a newer build (format or version); refusing to overwrite slot %s"), *File, *Slot);
			return false;
		}
		if (Existing)
		{
			MaxSequence = FMath::Max(MaxSequence, Existing->Sequence);
		}
	}
	if (!Data->Migrate())
	{
		return false;
	}
	Data->Sequence = MaxSequence + 1;
	Data->SavedAt = FDateTime::UtcNow();

	// 0. serialize, check it reads back as a save, wrap with header + checksum
	TArray<uint8> Payload, File;
	if (!UGameplayStatics::SaveGameToMemory(Data, Payload) || !Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromMemory(Payload)))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: %s did not serialize cleanly; nothing written"), *Slot);
		return false;
	}
	Wrap(Payload, Data->Sequence, File);
	// 1. temp copy, read back
	const FString Tmp = Slot + TEXT("_tmp");
	if (!WriteVerified(File, Tmp))
	{
		UGameplayStatics::DeleteGameInSlot(Tmp, 0);
		UE_LOG(LogTemp, Error, TEXT("CDSave: could not write %s; nothing committed"), *Tmp);
		return false;
	}
	// 2. back up the current main byte-for-byte, only if it is Valid. Failure = rollback: _tmp deleted, nothing committed.
	TArray<uint8> Old;
	UCDSaveGame* OldData = nullptr;
	if (Inspect(Slot, OldData) == ECDSaveFileStatus::Valid && ReadBytes(Slot, Old))
	{
		if (!WriteVerified(Old, Slot + TEXT("_bak")))
		{
			UGameplayStatics::DeleteGameInSlot(Tmp, 0);
			UE_LOG(LogTemp, Error, TEXT("CDSave: backup of %s failed; rolled back, main untouched, nothing committed"), *Slot);
			return false;
		}
	}
	else if (UGameplayStatics::DoesSaveGameExist(Slot, 0))
	{
		UE_LOG(LogTemp, Warning, TEXT("CDSave: %s was corrupt; keeping the existing %s_bak, overwriting main"), *Slot, *Slot);
	}
	// 3. main. Failure: the verified _tmp is kept as recoverable progress (documented in the header).
	if (!WriteVerified(File, Slot))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: writing %s failed; the verified %s (sequence %lld) is kept and will be recovered"), *Slot, *Tmp, Data->Sequence);
		return false;
	}
	// 4. commit done
	UGameplayStatics::DeleteGameInSlot(Tmp, 0);
	Current = Data;
	return true;
}
