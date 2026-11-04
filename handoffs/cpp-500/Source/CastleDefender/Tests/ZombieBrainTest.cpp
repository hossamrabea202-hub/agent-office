// #500 point 6: automated tests. Run in the editor: Tools > Session Frontend > Automation, filter "CastleDefender", or from the command line:
//   UnrealEditor-Cmd.exe "<project>.uproject" -ExecCmds="Automation RunTests CastleDefender; Quit" -unattended -nopause -nullrhi -ReportExportPath="<folder>"
// Pure tests: the zombie target rule (no map, no Play) and the save path (writes and deletes its own test slots).
// Still to add once the module builds (they need a world): pool lifecycle (delayed + immediate release + reacquire, duplicate release,
// destroyed while pending, cross-world, capacity, OnReleased destroys) and one PIE test (zombie registers, picks a target, unregisters, no stale ref).
#include "Misc/AutomationTest.h"
#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Guid.h"
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
	UCDSaveSubsystem* Saves = NewObject<UCDSaveSubsystem>(GetTransientPackage());

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
	UCDSaveSubsystem* Fresh = NewObject<UCDSaveSubsystem>(GetTransientPackage());
	TestFalse(TEXT("fresh object over a newer on-disk save is refused"), Fresh->Save(Make(1), Slot));
	const UCDSaveGame* StillNewer = UCDSaveSubsystem::LoadValid(Slot);
	if (TestNotNull(TEXT("newer save still there"), StillNewer)) { TestEqual(TEXT("newer version kept"), StillNewer->SaveVersion, UCDSaveGame::CurrentVersion + 1); }
	TestTrue(TEXT("that slot is now read-only"), Fresh->IsReadOnly(Slot));
	const FString Other = Slot + TEXT("B");
	TestTrue(TEXT("another slot is still writable (read-only is per slot)"), Fresh->Save(Make(2), Other) && !Fresh->IsReadOnly(Other));
	for (const FString& F : { Other, Other + TEXT("_tmp"), Other + TEXT("_bak") }) { UGameplayStatics::DeleteGameInSlot(F, 0); }

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
