#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"

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

UCDSaveGame* UCDSaveSubsystem::LoadValid(const FString& Slot)
{
	if (!UGameplayStatics::DoesSaveGameExist(Slot, 0))
	{
		return nullptr;
	}
	return Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot, 0));
}

UCDSaveGame* UCDSaveSubsystem::LoadOrCreate(const FString& Slot)
{
	bReadOnly = false;
	UCDSaveGame* Data = LoadValid(Slot);
	if (!Data)
	{
		if (UGameplayStatics::DoesSaveGameExist(Slot, 0))
		{
			UE_LOG(LogTemp, Warning, TEXT("CDSave: %s is unreadable; trying %s_bak (the main file is left as it is)"), *Slot, *Slot);
		}
		Data = LoadValid(Slot + TEXT("_bak"));
	}
	if (Data && !Data->Migrate())
	{
		bReadOnly = true;
		UE_LOG(LogTemp, Error, TEXT("CDSave: %s is version %d, newer than this build (%d): loaded read-only"), *Slot, Data->SaveVersion, UCDSaveGame::CurrentVersion);
	}
	if (!Data)
	{
		Data = Cast<UCDSaveGame>(UGameplayStatics::CreateSaveGameObject(UCDSaveGame::StaticClass()));
	}
	Current = Data;
	return Data;
}

static bool ReadBytes(const FString& Slot, TArray<uint8>& Out)
{
	Out.Reset();
	return UGameplayStatics::DoesSaveGameExist(Slot, 0) && UGameplayStatics::LoadDataFromSlot(Out, Slot, 0) && Out.Num() > 0;
}

static bool WriteVerified(const TArray<uint8>& Bytes, const FString& Slot)
{
	TArray<uint8> Back;
	return UGameplayStatics::SaveDataToSlot(Bytes, Slot, 0) && ReadBytes(Slot, Back) && Back == Bytes;
}

bool UCDSaveSubsystem::Save(UCDSaveGame* Data, const FString& Slot)
{
	if (!Data)
	{
		return false;
	}
	if (bReadOnly || Data->IsNewerThanBuild())
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: refusing to overwrite %s: it holds a save from a newer build"), *Slot);
		return false;
	}
	Data->SaveVersion = UCDSaveGame::CurrentVersion;
	Data->SavedAt = FDateTime::UtcNow();

	// 1. serialize and verify in memory
	TArray<uint8> Bytes;
	if (!UGameplayStatics::SaveGameToMemory(Data, Bytes) || !Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes)))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: %s did not serialize cleanly; nothing written"), *Slot);
		return false;
	}
	// 2. temp slot, read back
	const FString Tmp = Slot + TEXT("_tmp");
	if (!WriteVerified(Bytes, Tmp))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: could not write %s; main untouched"), *Tmp);
		return false;
	}
	// 3. back up the current main save byte-for-byte, only if it is a valid save (a corrupt main never replaces a good backup)
	TArray<uint8> Old;
	if (ReadBytes(Slot, Old))
	{
		if (Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromMemory(Old)))
		{
			if (!WriteVerified(Old, Slot + TEXT("_bak")))
			{
				UE_LOG(LogTemp, Error, TEXT("CDSave: backup of %s failed; main untouched"), *Slot);
				return false;
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("CDSave: %s was unreadable; keeping the existing %s_bak"), *Slot, *Slot);
		}
	}
	// 4. main
	if (!WriteVerified(Bytes, Slot))
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: writing %s failed; the verified %s_bak holds the last good save, %s_tmp the new one"), *Slot, *Slot, *Tmp);
		return false;
	}
	UGameplayStatics::DeleteGameInSlot(Tmp, 0);
	Current = Data;
	return true;
}
