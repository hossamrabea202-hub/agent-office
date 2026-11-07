// #500 point 6: automated tests. Run in the editor: Tools > Session Frontend > Automation, filter "CastleDefender", or from the command line:
//   UnrealEditor-Cmd.exe "<project>.uproject" -ExecCmds="Automation RunTests CastleDefender; Quit" -unattended -nopause -nullrhi -ReportExportPath="<folder>"
// Pure tests: the zombie target rule (no map, no Play) and the save path (writes and deletes its own test slots).
// Still to add once the module builds (they need a world): pool lifecycle (delayed + immediate release + reacquire, duplicate release,
// destroyed while pending, cross-world, capacity, OnReleased destroys) and one PIE test (zombie registers, picks a target, unregisters, no stale ref).
#include "Misc/AutomationTest.h"
#include "CDSaveGame.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "ZombieBase.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace CDTest
{
	using FC = AZombieBase::FCandidate;
	const float SR = 2500.f, SH = 250.f, FR = 2500.f;
	int32 Pick(const FVector* Player, const TArray<FC>& S, const TArray<FC>& F, bool bNoPlayerBlocks = true)
	{
		return AZombieBase::ChooseTarget(FVector::ZeroVector, Player, S, F, SR, SH, FR, bNoPlayerBlocks);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDZombieTargetTest, "CastleDefender.Zombie.ChooseTarget",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCDZombieTargetTest::RunTest(const FString& Parameters)
{
	using namespace CDTest;
	const FVector Player(5000, 0, 0);

	TestEqual(TEXT("no soldiers or farmers: keep the player"), Pick(&Player, {}, {}), INDEX_NONE);

	TArray<FC> S = { FC{ FVector(1000, 0, 0) }, FC{ FVector(500, 0, 0) } };
	TestEqual(TEXT("nearest soldier in range wins"), Pick(&Player, S, {}), 1);

	S[1].bDyingOrDead = true;
	TestEqual(TEXT("dying soldier is skipped"), Pick(&Player, S, {}), 0);

	TArray<FC> Invalid = { FC{ FVector(100, 0, 0), false } };
	TestEqual(TEXT("invalid soldier is skipped"), Pick(&Player, Invalid, {}), INDEX_NONE);

	TestEqual(TEXT("soldier 400 cm higher (on the wall) is skipped"), Pick(&Player, { FC{ FVector(300, 0, 400) } }, {}), INDEX_NONE);
	TestEqual(TEXT("height difference exactly at the limit (250) is skipped"), Pick(&Player, { FC{ FVector(300, 0, 250) } }, {}), INDEX_NONE);
	TestEqual(TEXT("height difference just under the limit is taken"), Pick(&Player, { FC{ FVector(300, 0, 249) } }, {}), 0);

	TestEqual(TEXT("soldier beyond the range is skipped"), Pick(&Player, { FC{ FVector(3000, 0, 0) } }, {}), INDEX_NONE);
	TestEqual(TEXT("soldier exactly at the range (2500) is skipped (strict <)"), Pick(&Player, { FC{ FVector(2500, 0, 0) } }, {}), INDEX_NONE);
	TestEqual(TEXT("soldier just inside the range is taken"), Pick(&Player, { FC{ FVector(2499, 0, 0) } }, {}), 0);

	TestEqual(TEXT("equal distance: the first soldier wins"), Pick(&Player, { FC{ FVector(800, 0, 0) }, FC{ FVector(0, 800, 0) } }, {}), 0);
	TestEqual(TEXT("equal distance soldier vs farmer: the soldier wins"), Pick(&Player, { FC{ FVector(800, 0, 0) } }, { FC{ FVector(0, 800, 0) } }), 0);

	TestEqual(TEXT("nearer farmer beats a soldier (index after soldiers)"), Pick(&Player, S, { FC{ FVector(200, 0, 0) } }), S.Num());
	TArray<FC> DeadFarmer = { FC{ FVector(200, 0, 0), true, true } };
	TestEqual(TEXT("dead farmer is skipped"), Pick(&Player, S, DeadFarmer), 0);

	const FVector NearPlayer(100, 0, 0);
	TestEqual(TEXT("player nearer than everyone: keep the player"), Pick(&NearPlayer, S, { FC{ FVector(200, 0, 0) } }), INDEX_NONE);

	TestEqual(TEXT("no player, Blueprint parity: nothing is picked"), Pick(nullptr, S, {}), INDEX_NONE);
	TestEqual(TEXT("no player, alternative rule: the nearest valid target is picked"), Pick(nullptr, S, {}, false), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDSaveTest, "CastleDefender.Save.SafeWritePath",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCDSaveTest::RunTest(const FString& Parameters)
{
	// A fresh slot name per run: the test can never delete real or older test data.
	const FString Slot = FString::Printf(TEXT("CDTest_%s"), *FGuid::NewGuid().ToString(EGuidFormats::Digits));
	const FString Tmp = Slot + TEXT("_tmp"), Bak = Slot + TEXT("_bak");
	auto Clean = [&]() { for (const FString& F : { Slot, Tmp, Bak }) { UGameplayStatics::DeleteGameInSlot(F, 0); } };
	auto Make = [](int32 Gold, int32 Version = UCDSaveGame::CurrentVersion)
	{
		UCDSaveGame* D = Cast<UCDSaveGame>(UGameplayStatics::CreateSaveGameObject(UCDSaveGame::StaticClass()));
		D->SetInt(TEXT("Gold"), Gold);
		D->SaveVersion = Version;
		return D;
	};
	// Writes a valid enveloped file directly (to set up recovery cases).
	auto WriteRaw = [](UCDSaveGame* D, int64 Seq, const FString& File)
	{
		D->Sequence = Seq;
		TArray<uint8> Payload, Out;
		UGameplayStatics::SaveGameToMemory(D, Payload);
		UCDSaveSubsystem::Wrap(Payload, Seq, Out);
		return UGameplayStatics::SaveDataToSlot(Out, File, 0);
	};
	// Null-safe check of one file's Gold.
	auto ExpectGold = [this](const FString& What, const FString& File, int32 Gold)
	{
		const UCDSaveGame* L = UCDSaveSubsystem::LoadValid(File);
		if (TestNotNull(*(What + TEXT(" (loads)")), L)) { TestEqual(*What, L->GetInt(TEXT("Gold"), -1), Gold); }
	};
	auto ExpectLoaded = [this](const FString& What, const UCDSaveGame* L, int32 Gold)
	{
		if (TestNotNull(*(What + TEXT(" (object)")), L)) { TestEqual(*What, L->GetInt(TEXT("Gold"), -1), Gold); }
	};
	const TArray<uint8> Garbage = { 1, 2, 3, 4, 5, 6, 7, 8 };
	// Game instance subsystems must live inside a game instance (ClassWithin); the subsystem's own code never touches it.
	UGameInstance* GameInstance = NewObject<UGameInstance>(GetTransientPackage());
	// The refusal and forced-failure cases below log errors on purpose.
	for (const TCHAR* Msg : { TEXT("from a newer build or another save class"), TEXT("holds a save this build cannot write safely"),
		TEXT("refusing to write"), TEXT("failed; main untouched"), TEXT("failed; the verified") })
	{
		AddExpectedMessage(Msg, ELogVerbosity::Error, EAutomationExpectedMessageFlags::Contains, 0, false);
	}
	UCDSaveSubsystem* Saves = NewObject<UCDSaveSubsystem>(GameInstance);

	Clean();
	ExpectLoaded(TEXT("missing save -> fresh default"), Saves->LoadOrCreate(Slot), -1);

	TestTrue(TEXT("first save works"), Saves->Save(Make(10), Slot));
	TestTrue(TEXT("second save works"), Saves->Save(Make(20), Slot));
	ExpectGold(TEXT("main holds the newest"), Slot, 20);
	ExpectGold(TEXT("backup holds the previous"), Bak, 10);
	TestFalse(TEXT("temp file removed after commit"), UGameplayStatics::DoesSaveGameExist(Tmp, 0));

	// checksum: one flipped byte makes the file invalid
	TArray<uint8> Bytes;
	UGameplayStatics::LoadDataFromSlot(Bytes, Slot, 0);
	if (TestTrue(TEXT("main file has bytes"), Bytes.Num() > 30))
	{
		Bytes.Last() ^= 0xFF;
		UGameplayStatics::SaveDataToSlot(Bytes, Slot, 0);
		TestNull(TEXT("flipped byte -> invalid (CRC)"), UCDSaveSubsystem::LoadValid(Slot));
	}
	ExpectLoaded(TEXT("corrupt main -> verified backup is loaded"), Saves->LoadOrCreate(Slot), 10);
	TestTrue(TEXT("save over a corrupt main works"), Saves->Save(Make(30), Slot));
	ExpectGold(TEXT("corrupt main did not replace the good backup"), Bak, 10);

	UGameplayStatics::SaveDataToSlot(Garbage, Bak, 0);
	ExpectLoaded(TEXT("corrupt backup never replaces a valid main"), Saves->LoadOrCreate(Slot), 30);

	// Bug B: an interrupted save leaves a verified _tmp that is newer than main
	Clean();
	WriteRaw(Make(40), 4, Slot);
	WriteRaw(Make(50), 5, Tmp);
	ExpectLoaded(TEXT("_tmp newer than main (commit interrupted) -> _tmp recovered"), Saves->LoadOrCreate(Slot), 50);
	Clean();
	WriteRaw(Make(60), 6, Slot);
	WriteRaw(Make(55), 5, Tmp);
	ExpectLoaded(TEXT("stale _tmp older than main -> main wins"), Saves->LoadOrCreate(Slot), 60);
	Clean();
	WriteRaw(Make(70), 7, Tmp);
	ExpectLoaded(TEXT("first save interrupted, only _tmp exists -> _tmp recovered"), Saves->LoadOrCreate(Slot), 70);
	TestTrue(TEXT("saving after recovery continues the sequence"), Saves->Save(Make(71), Slot));
	const UCDSaveGame* AfterRecovery = UCDSaveSubsystem::LoadValid(Slot);
	if (TestNotNull(TEXT("main after recovery save"), AfterRecovery)) { TestTrue(TEXT("sequence > 7"), AfterRecovery->Sequence > 7); }

	// Bug A: a fresh object must not overwrite a newer build's save on disk, even without LoadOrCreate first
	Clean();
	WriteRaw(Make(99, UCDSaveGame::CurrentVersion + 1), 3, Slot);
	UCDSaveSubsystem* Fresh = NewObject<UCDSaveSubsystem>(GameInstance);
	TestFalse(TEXT("fresh object over a newer on-disk save is refused"), Fresh->Save(Make(1), Slot));
	const UCDSaveGame* StillNewer = UCDSaveSubsystem::LoadValid(Slot);
	if (TestNotNull(TEXT("newer save still there"), StillNewer)) { TestEqual(TEXT("newer version kept"), StillNewer->SaveVersion, UCDSaveGame::CurrentVersion + 1); }
	TestTrue(TEXT("that slot is now read-only"), Fresh->IsReadOnly(Slot));
	const FString Other = Slot + TEXT("B");
	TestTrue(TEXT("another slot is still writable (read-only is per slot)"), Fresh->Save(Make(2), Other) && !Fresh->IsReadOnly(Other));
	for (const FString& F : { Other, Other + TEXT("_tmp"), Other + TEXT("_bak") }) { UGameplayStatics::DeleteGameInSlot(F, 0); }

	// Rev 4: an envelope format newer than this build is protected, not treated as invalid
	Clean();
	{
		TArray<uint8> Payload, Env;
		UCDSaveGame* Future = Make(77);
		Future->Sequence = 2;
		UGameplayStatics::SaveGameToMemory(Future, Payload);
		UCDSaveSubsystem::Wrap(Payload, 2, Env);
		Env[4] = 0x7F;   // format field (bytes 4..7) -> a future format
		UGameplayStatics::SaveDataToSlot(Env, Slot, 0);
		UCDSaveGame* Seen = nullptr;
		TestEqual(TEXT("future envelope format -> UnsupportedFormat"), (int32)UCDSaveSubsystem::Inspect(Slot, Seen), (int32)ECDSaveFileStatus::UnsupportedFormat);
		UCDSaveSubsystem* Older = NewObject<UCDSaveSubsystem>(GameInstance);
		Older->LoadOrCreate(Slot);
		TestTrue(TEXT("future format makes the slot read-only"), Older->IsReadOnly(Slot));
		TestFalse(TEXT("future format is never overwritten"), Older->Save(Make(1), Slot));
		TArray<uint8> After;
		UGameplayStatics::LoadDataFromSlot(After, Slot, 0);
		TestTrue(TEXT("future file bytes unchanged"), After == Env);
	}

	// Rev 4: header sequence must match the save's own sequence; a changed header byte fails the checksum
	Clean();
	{
		TArray<uint8> Payload, Env;
		UCDSaveGame* D = Make(88);
		D->Sequence = 3;
		UGameplayStatics::SaveGameToMemory(D, Payload);
		UCDSaveSubsystem::Wrap(Payload, 9, Env);   // header says 9, payload says 3
		UGameplayStatics::SaveDataToSlot(Env, Slot, 0);
		UCDSaveGame* Seen = nullptr;
		TestEqual(TEXT("header / payload sequence mismatch -> Corrupt"), (int32)UCDSaveSubsystem::Inspect(Slot, Seen), (int32)ECDSaveFileStatus::Corrupt);
		UCDSaveSubsystem::Wrap(Payload, 3, Env);
		Env[8] ^= 0x01;                             // flip a bit inside the header sequence field
		UGameplayStatics::SaveDataToSlot(Env, Slot, 0);
		TestEqual(TEXT("changed header byte -> Corrupt (CRC covers the header)"), (int32)UCDSaveSubsystem::Inspect(Slot, Seen), (int32)ECDSaveFileStatus::Corrupt);
	}
	// Empty file: Corrupt, not Missing
	Clean();
	{
		const FString Path = FPaths::ProjectSavedDir() / TEXT("SaveGames") / (Slot + TEXT(".sav"));
		FFileHelper::SaveStringToFile(FString(), *Path);
		UCDSaveGame* Seen = nullptr;
		TestTrue(TEXT("empty file exists"), UGameplayStatics::DoesSaveGameExist(Slot, 0));
		TestEqual(TEXT("empty file -> Corrupt (not Missing)"), (int32)UCDSaveSubsystem::Inspect(Slot, Seen), (int32)ECDSaveFileStatus::Corrupt);
	}

	// Garbage without an envelope used to crash the process inside LoadGameFromMemory (first real run): now Corrupt
	Clean();
	UGameplayStatics::SaveDataToSlot(Garbage, Slot, 0);
	{
		UCDSaveGame* Seen = nullptr;
		TestEqual(TEXT("unenveloped garbage -> Corrupt, no crash"), (int32)UCDSaveSubsystem::Inspect(Slot, Seen), (int32)ECDSaveFileStatus::Corrupt);
	}

	// Another class's save (the game's own saves are BP_CastleSave): never overwritten
	Clean();
	{
		TArray<uint8> ForeignBytes;
		UGameplayStatics::SaveGameToMemory(Make(1), ForeignBytes);
		// Rewrite the class name in the engine save header to another existing class: /Script/Engine.SaveGame.
		const FString Ours = UCDSaveGame::StaticClass()->GetPathName();
		const FTCHARToUTF8 OursUtf8(*Ours);
		int32 At = INDEX_NONE;
		for (int32 i = 4; i + OursUtf8.Length() <= ForeignBytes.Num() && At == INDEX_NONE; ++i)
		{
			if (FMemory::Memcmp(ForeignBytes.GetData() + i, OursUtf8.Get(), OursUtf8.Length()) == 0) { At = i; }
		}
		if (TestTrue(TEXT("class name found in the save header"), At != INDEX_NONE))
		{
			const FTCHARToUTF8 OtherClass(TEXT("/Script/Engine.SaveGame"));
			TArray<uint8> Patched;
			Patched.Append(ForeignBytes.GetData(), At - 4);
			const int32 Len = OtherClass.Length() + 1;
			Patched.Append(reinterpret_cast<const uint8*>(&Len), 4);
			Patched.Append(reinterpret_cast<const uint8*>(OtherClass.Get()), OtherClass.Length());
			Patched.Add(0);
			Patched.Append(ForeignBytes.GetData() + At + OursUtf8.Length() + 1, ForeignBytes.Num() - (At + OursUtf8.Length() + 1));
			UGameplayStatics::SaveDataToSlot(Patched, Slot, 0);
			UCDSaveGame* Seen = nullptr;
			TestEqual(TEXT("another class's save -> ForeignSave"), (int32)UCDSaveSubsystem::Inspect(Slot, Seen), (int32)ECDSaveFileStatus::ForeignSave);
			UCDSaveSubsystem* S2 = NewObject<UCDSaveSubsystem>(GameInstance);
			TestFalse(TEXT("a foreign save is never overwritten"), S2->Save(Make(2), Slot));
			TestTrue(TEXT("its slot becomes read-only"), S2->IsReadOnly(Slot));
			TArray<uint8> After;
			UGameplayStatics::LoadDataFromSlot(After, Slot, 0);
			TestTrue(TEXT("foreign file bytes unchanged"), After == Patched);
		}
	}

	// Commit point: once _tmp is verified, a later failure (backup or main write) keeps it and the next load recovers it.
	// The failure is forced by making the target file read-only on disk.
	{
		IPlatformFile& PF = FPlatformFileManager::Get().GetPlatformFile();
		const FString Dir = FPaths::ProjectSavedDir() / TEXT("SaveGames");
		for (const FString& Target : { Bak, Slot })
		{
			Clean();
			TestTrue(TEXT("setup save 1"), Saves->Save(Make(100), Slot));
			TestTrue(TEXT("setup save 2"), Saves->Save(Make(200), Slot));   // main 200, bak 100
			const FString Path = Dir / (Target + TEXT(".sav"));
			PF.SetReadOnly(*Path, true);
			const bool bSaved = Saves->Save(Make(300), Slot);
			PF.SetReadOnly(*Path, false);
			const FString What = Target == Bak ? TEXT("backup write fails") : TEXT("main write fails");
			TestFalse(*(What + TEXT(": Save returns false")), bSaved);
			ExpectGold(What + TEXT(": verified _tmp kept"), Tmp, 300);
			ExpectGold(What + TEXT(": main still the previous save"), Slot, 200);
			UCDSaveSubsystem* Next = NewObject<UCDSaveSubsystem>(GameInstance);
			ExpectLoaded(What + TEXT(": next load recovers the committed _tmp"), Next->LoadOrCreate(Slot), 300);
			TestTrue(What + TEXT(": the following save succeeds"), Next->Save(Make(400), Slot));
			ExpectGold(What + TEXT(": main updated"), Slot, 400);
			TestFalse(What + TEXT(": _tmp cleaned"), UGameplayStatics::DoesSaveGameExist(Tmp, 0));
		}
	}

	// Bug F: an old-version object passed straight to Save is migrated, not just relabelled
	Clean();
	UCDSaveGame* Old = Make(5, 0);
	TestTrue(TEXT("old-version object saves"), Saves->Save(Old, Slot));
	TestEqual(TEXT("it was migrated to the current version"), Old->SaveVersion, UCDSaveGame::CurrentVersion);

	UCDSaveGame* M = Make(5, 1);
	TestTrue(TEXT("migration runs"), M->Migrate());
	TestTrue(TEXT("migration is repeatable"), M->Migrate() && M->SaveVersion == UCDSaveGame::CurrentVersion && M->GetInt(TEXT("Gold")) == 5);

	Clean();
	return true;
}

#endif
