#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"

bool UCDSaveGame::Migrate()
{
	if (SaveVersion > CurrentVersion)
	{
		return false;
	}
	// Add one step per version bump, oldest first. Example for a future version 2:
	// if (SaveVersion < 2) { Ints.Add(TEXT("Gems"), 0); SaveVersion = 2; }
	SaveVersion = CurrentVersion;
	return true;
}

UCDSaveGame* UCDSaveSubsystem::LoadOrCreate(const FString& Slot)
{
	UCDSaveGame* Data = nullptr;
	if (UGameplayStatics::DoesSaveGameExist(Slot, 0))
	{
		Data = Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot, 0));
	}
	if (!Data && UGameplayStatics::DoesSaveGameExist(Slot + TEXT("_bak"), 0))
	{
		UE_LOG(LogTemp, Warning, TEXT("CDSave: %s unreadable, using %s_bak"), *Slot, *Slot);
		Data = Cast<UCDSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot + TEXT("_bak"), 0));
	}
	if (Data && !Data->Migrate())
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: %s is version %d, newer than this build (%d); loaded read-only"), *Slot, Data->SaveVersion, UCDSaveGame::CurrentVersion);
	}
	if (!Data)
	{
		Data = Cast<UCDSaveGame>(UGameplayStatics::CreateSaveGameObject(UCDSaveGame::StaticClass()));
	}
	Current = Data;
	return Data;
}

bool UCDSaveSubsystem::Save(UCDSaveGame* Data, const FString& Slot)
{
	if (!Data)
	{
		return false;
	}
	if (Data->SaveVersion > UCDSaveGame::CurrentVersion)
	{
		UE_LOG(LogTemp, Error, TEXT("CDSave: refusing to overwrite %s with a newer-version save"), *Slot);
		return false;
	}
	if (UGameplayStatics::DoesSaveGameExist(Slot, 0))
	{
		if (USaveGame* Old = UGameplayStatics::LoadGameFromSlot(Slot, 0))
		{
			UGameplayStatics::SaveGameToSlot(Old, Slot + TEXT("_bak"), 0);
		}
	}
	Data->SaveVersion = UCDSaveGame::CurrentVersion;
	Data->SavedAt = FDateTime::UtcNow();
	Current = Data;
	return UGameplayStatics::SaveGameToSlot(Data, Slot, 0);
}
