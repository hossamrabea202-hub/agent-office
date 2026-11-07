#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Crc.h"
#include "Misc/EngineVersion.h"
#include "Serialization/CustomVersion.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"
#include "UObject/ObjectVersion.h"
#include "UObject/SoftObjectPtr.h"

namespace
{
	const uint32 EnvelopeMagic = 0x56534443;   // "CDSV" little-endian
	const uint32 EnvelopeFormat = 2;           // 2 = CRC over header fields + payload (format 1 was never shipped)
	const int32 EnvelopeHeaderFieldsSize = 4 + 4 + 8 + 4;  // magic, format, sequence, length
	const int32 EnvelopeHeaderSize = EnvelopeHeaderFieldsSize + 4;  // + CRC

	bool ReadBytes(const FString& SlotFile, TArray<uint8>& Out)
	{
		Out.Reset();
		return UGameplayStatics::DoesSaveGameExist(SlotFile, 0) && UGameplayStatics::LoadDataFromSlot(Out, SlotFile, 0) && Out.Num() > 0;
	}

	// UGameplayStatics::LoadGameFromMemory trusts its input: in the first real test run an 8-byte garbage file was read as a 67-million-character
	// class name and the editor died on a fatal FName assert. Every payload goes through LoadPayload instead: all lengths are bounded by the
	// buffer, the header's class is checked before anything is created, and names / object references that UCDSaveGame never writes are refused.
	const int32 SaveGameFileTag = 0x53415647;          // the engine's save tag (private in GameplayStatics.cpp)
	const int32 MaxKnownSaveGameFileVersion = 3;       // FSaveGameFileVersion::PackageFileSummaryVersionChange, the latest in 5.8

	class FBoundedSaveReader final : public FObjectAndNameAsStringProxyArchive
	{
	public:
		explicit FBoundedSaveReader(FArchive& Inner) : FObjectAndNameAsStringProxyArchive(Inner, false) {}

		virtual FArchive& operator<<(FName& N) override
		{
			FString S;
			InnerArchive << S;
			if (InnerArchive.IsError() || S.Len() >= NAME_SIZE)
			{
				SetError();                 // FName(*S) would assert on an over-long string
				N = NAME_None;
				return *this;
			}
			N = FName(*S);
			return *this;
		}
		// UCDSaveGame holds no object references: one in the stream means these bytes were not written by it.
		virtual FArchive& operator<<(UObject*& Obj) override { Obj = nullptr; SetError(); return *this; }
		virtual FArchive& operator<<(FObjectPtr& Obj) override { Obj = nullptr; SetError(); return *this; }
		virtual FArchive& operator<<(FWeakObjectPtr& Obj) override { Obj.Reset(); SetError(); return *this; }
		virtual FArchive& operator<<(FSoftObjectPtr& Value) override { Value.Reset(); SetError(); return *this; }
		virtual FArchive& operator<<(FSoftObjectPath& Value) override { Value.Reset(); SetError(); return *this; }
	};

	enum class EPayload : uint8 { Loaded, Garbage, ForeignClass, NewerEngine };

	EPayload LoadPayload(const TArray<uint8>& Payload, UCDSaveGame*& Out)
	{
		Out = nullptr;
		FMemoryReader R(Payload, true);
		R.ArMaxSerializeSize = Payload.Num();      // no string or array in this buffer can be longer than the buffer
		int32 Tag = 0, FileVersion = 0;
		R << Tag;
		if (R.IsError() || Tag != SaveGameFileTag)
		{
			return EPayload::Garbage;              // untagged saves predate UE4's save header; nothing in this project wrote one
		}
		R << FileVersion;
		if (FileVersion > MaxKnownSaveGameFileVersion)
		{
			return EPayload::NewerEngine;
		}
		if (R.IsError() || FileVersion < 1)
		{
			return EPayload::Garbage;
		}
		FPackageFileVersion PackageVersion;
		if (FileVersion >= 3)
		{
			R << PackageVersion;
		}
		else
		{
			int32 OldUE4Version = 0;
			R << OldUE4Version;
			PackageVersion = FPackageFileVersion::CreateUE4Version(OldUE4Version);
		}
		FEngineVersion EngineVersion;
		R << EngineVersion;
		if (R.IsError())
		{
			return EPayload::Garbage;
		}
		if (!GPackageFileUEVersion.IsCompatible(PackageVersion))
		{
			return EPayload::NewerEngine;          // written by a newer engine: this one cannot read it reliably
		}
		R.SetUEVer(PackageVersion);
		R.SetEngineVer(EngineVersion);
		if (FileVersion >= 2)
		{
			int32 Format = 0;
			R << Format;
			// FCustomVersionContainer::Serialize check()s on an unknown format: validate it first
			if (R.IsError() || Format <= (int32)ECustomVersionSerializationFormat::Unknown || Format > (int32)ECustomVersionSerializationFormat::Latest)
			{
				return EPayload::Garbage;
			}
			FCustomVersionContainer Versions;
			Versions.Serialize(R, (ECustomVersionSerializationFormat)Format);
			if (R.IsError())
			{
				return EPayload::Garbage;
			}
			R.SetCustomVersions(Versions);
		}
		FString ClassName;
		R << ClassName;
		if (R.IsError() || ClassName.IsEmpty() || ClassName.Len() >= NAME_SIZE)
		{
			return EPayload::Garbage;
		}
		// Find only, never load: an unknown class (for example the game's Blueprint save BP_CastleSave_C) is someone else's save.
		UClass* Class = UClass::TryFindTypeSlow<UClass>(ClassName);
		if (!Class || !Class->IsChildOf(UCDSaveGame::StaticClass()) || Class->HasAnyClassFlags(CLASS_Abstract))
		{
			return EPayload::ForeignClass;
		}
		UCDSaveGame* Data = NewObject<UCDSaveGame>(GetTransientPackage(), Class);
		FBoundedSaveReader Ar(R);
		Data->Serialize(Ar);
		if (R.IsError() || Ar.IsError())
		{
			return EPayload::Garbage;
		}
		Out = Data;
		return EPayload::Loaded;
	}

	bool WriteVerified(const TArray<uint8>& Bytes, const FString& SlotFile)
	{
		TArray<uint8> Back;
		return UGameplayStatics::SaveDataToSlot(Bytes, SlotFile, 0) && ReadBytes(SlotFile, Back) && Back == Bytes;
	}

	uint32 EnvelopeCrc(const uint8* HeaderFields, const uint8* Payload, int32 PayloadLen)
	{
		return FCrc::MemCrc32(Payload, PayloadLen, FCrc::MemCrc32(HeaderFields, EnvelopeHeaderFieldsSize));
	}

	// The three files of one slot, in tie-break order.
	TArray<FString, TInlineAllocator<3>> SlotFiles(const FString& Slot)
	{
		return { Slot, Slot + TEXT("_tmp"), Slot + TEXT("_bak") };
	}

	bool Blocks(ECDSaveFileStatus S)
	{
		return S == ECDSaveFileStatus::UnsupportedFormat || S == ECDSaveFileStatus::NewerVersion || S == ECDSaveFileStatus::ForeignSave;
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
	Out.Reset(EnvelopeHeaderSize + Payload.Num());
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
	if (File.Num() < EnvelopeHeaderSize)
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
	if ((int64)Len != (int64)File.Num() - EnvelopeHeaderSize || EnvelopeCrc(File.GetData(), File.GetData() + EnvelopeHeaderSize, Len) != Crc)
	{
		return ECDSaveFileStatus::Corrupt;
	}
	OutPayload.Append(File.GetData() + EnvelopeHeaderSize, Len);
	return ECDSaveFileStatus::Valid;
}

ECDSaveFileStatus UCDSaveSubsystem::Inspect(const FString& SlotFile, UCDSaveGame*& OutData)
{
	OutData = nullptr;
	if (!UGameplayStatics::DoesSaveGameExist(SlotFile, 0))
	{
		return ECDSaveFileStatus::Missing;
	}
	TArray<uint8> File, Payload;
	if (!UGameplayStatics::LoadDataFromSlot(File, SlotFile, 0))
	{
		return ECDSaveFileStatus::Unreadable;   // there, but the platform would not hand over its bytes (locked, permissions)
	}
	if (File.Num() == 0)
	{
		return ECDSaveFileStatus::Corrupt;      // an empty file is a damaged save, not a missing one
	}
	int64 HeaderSequence = 0;
	bool bLegacy = false;
	const ECDSaveFileStatus Envelope = Unwrap(File, Payload, HeaderSequence, bLegacy);
	if (Envelope != ECDSaveFileStatus::Valid)
	{
		return Envelope;
	}
	UCDSaveGame* Data = nullptr;
	switch (LoadPayload(Payload, Data))
	{
	case EPayload::Loaded:       break;
	case EPayload::ForeignClass: return ECDSaveFileStatus::ForeignSave;         // e.g. the game's BP_CastleSave: never ours to overwrite
	case EPayload::NewerEngine:  return ECDSaveFileStatus::UnsupportedFormat;   // written by a newer engine
	default:                     return ECDSaveFileStatus::Corrupt;
	}
	if (!bLegacy && Data->Sequence != HeaderSequence)
	{
		return ECDSaveFileStatus::Corrupt;   // the header and the save disagree on the sequence
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
		UE_LOG(LogTemp, Error, TEXT("CDSave: slot %s holds a save this build cannot write safely (newer format or version, or another save class): read-only"), *Slot);
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
			UE_LOG(LogTemp, Error, TEXT("CDSave: %s is from a newer build or another save class; refusing to overwrite slot %s"), *File, *Slot);
			return false;
		}
		if (Status == ECDSaveFileStatus::Unreadable)
		{
			// Its sequence is unknown and it may be the newest copy: do not guess. Not read-only, the next Save tries again.
			UE_LOG(LogTemp, Error, TEXT("CDSave: %s exists but cannot be read; not saving slot %s this time"), *File, *Slot);
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
	UCDSaveGame* RoundTrip = nullptr;
	if (!UGameplayStatics::SaveGameToMemory(Data, Payload) || LoadPayload(Payload, RoundTrip) != EPayload::Loaded)
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: %s did not serialize cleanly; nothing written"), *Slot);
		return false;
	}
	Wrap(Payload, Data->Sequence, File);
	// 1. temp copy, read back. Unverified bytes are removed; they could only be a partial write.
	const FString Tmp = Slot + TEXT("_tmp");
	if (!WriteVerified(File, Tmp))
	{
		UGameplayStatics::DeleteGameInSlot(Tmp, 0);
		UE_LOG(LogTemp, Error, TEXT("CDSave: could not write %s; nothing committed"), *Tmp);
		return false;
	}
	// COMMIT POINT: from here on this sequence is recoverable. Every later failure (an error return or a crash) leaves the verified _tmp on disk
	// and the next LoadOrCreate picks it, because it carries the highest sequence. There is no rollback after this line.
	// 2. back up the current main byte-for-byte, only if it is Valid.
	TArray<uint8> Old;
	UCDSaveGame* OldData = nullptr;
	if (Inspect(Slot, OldData) == ECDSaveFileStatus::Valid && ReadBytes(Slot, Old))
	{
		if (!WriteVerified(Old, Slot + TEXT("_bak")))
		{
			UE_LOG(LogTemp, Error, TEXT("CDSave: backup of %s failed; main untouched, the verified %s (sequence %lld) is kept and will be recovered"), *Slot, *Tmp, Data->Sequence);
			return false;
		}
	}
	else if (UGameplayStatics::DoesSaveGameExist(Slot, 0))
	{
		UE_LOG(LogTemp, Warning, TEXT("CDSave: %s was corrupt; keeping the existing %s_bak, overwriting main"), *Slot, *Slot);
	}
	// 3. main.
	if (!WriteVerified(File, Slot))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: writing %s failed; the verified %s (sequence %lld) is kept and will be recovered"), *Slot, *Tmp, Data->Sequence);
		return false;
	}
	// 4. done. If the delete fails, _tmp and main hold the same sequence and main wins the tie.
	if (!UGameplayStatics::DeleteGameInSlot(Tmp, 0))
	{
		UE_LOG(LogTemp, Warning, TEXT("CDSave: could not delete %s after a complete save; harmless (same sequence as main)"), *Tmp);
	}
	Current = Data;
	return true;
}
