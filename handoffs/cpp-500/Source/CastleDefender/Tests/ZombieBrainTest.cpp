// #500 point 6: automated tests. Run in the editor: Tools > Session Frontend > Automation, filter "CastleDefender", or from the command line:
//   UnrealEditor-Cmd.exe "<project>.uproject" -ExecCmds="Automation RunTests CastleDefender; Quit" -unattended -nopause -nullrhi -ReportExportPath="<folder>"
// Pure tests: the zombie target rule (no map, no Play) and the save path (writes and deletes its own test slots).
// Still to add once the module builds (they need a world): pool lifecycle (delayed + immediate release + reacquire, duplicate release,
// destroyed while pending, cross-world, capacity, OnReleased destroys) and one PIE test (zombie registers, picks a target, unregisters, no stale ref).
#include "Misc/AutomationTest.h"
#include "CDSaveGame.h"
#include "Kismet/GameplayStatics.h"
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
	const FString Slot = TEXT("CDTest_Save");
	auto Clean = [&Slot]()
	{
		for (const TCHAR* Suffix : { TEXT(""), TEXT("_bak"), TEXT("_tmp") }) { UGameplayStatics::DeleteGameInSlot(Slot + Suffix, 0); }
	};
	auto Make = [](int32 Gold, int32 Version = UCDSaveGame::CurrentVersion)
	{
		UCDSaveGame* D = Cast<UCDSaveGame>(UGameplayStatics::CreateSaveGameObject(UCDSaveGame::StaticClass()));
		D->SetInt(TEXT("Gold"), Gold);
		D->SaveVersion = Version;
		return D;
	};
	const TArray<uint8> Garbage = { 1, 2, 3, 4, 5, 6, 7, 8 };
	UCDSaveSubsystem* Saves = NewObject<UCDSaveSubsystem>(GetTransientPackage());

	Clean();
	TestEqual(TEXT("missing save -> fresh default"), Saves->LoadOrCreate(Slot)->GetInt(TEXT("Gold"), -1), -1);

	TestTrue(TEXT("first save works"), Saves->Save(Make(10), Slot));
	TestTrue(TEXT("second save works"), Saves->Save(Make(20), Slot));
	TestEqual(TEXT("main holds the newest"), UCDSaveSubsystem::LoadValid(Slot)->GetInt(TEXT("Gold")), 20);
	TestEqual(TEXT("backup holds the previous"), UCDSaveSubsystem::LoadValid(Slot + TEXT("_bak"))->GetInt(TEXT("Gold")), 10);
	TestFalse(TEXT("temp slot removed"), UGameplayStatics::DoesSaveGameExist(Slot + TEXT("_tmp"), 0));

	UGameplayStatics::SaveDataToSlot(Garbage, Slot, 0);
	TestEqual(TEXT("corrupt main -> verified backup is loaded"), Saves->LoadOrCreate(Slot)->GetInt(TEXT("Gold")), 10);
	TestTrue(TEXT("save over a corrupt main works"), Saves->Save(Make(30), Slot));
	TestEqual(TEXT("corrupt main did not replace the good backup"), UCDSaveSubsystem::LoadValid(Slot + TEXT("_bak"))->GetInt(TEXT("Gold")), 10);

	UGameplayStatics::SaveDataToSlot(Garbage, Slot + TEXT("_bak"), 0);
	TestEqual(TEXT("corrupt backup never replaces a valid main"), Saves->LoadOrCreate(Slot)->GetInt(TEXT("Gold")), 30);

	Clean();
	UGameplayStatics::SaveGameToSlot(Make(99, UCDSaveGame::CurrentVersion + 1), Slot, 0);
	Saves->LoadOrCreate(Slot);
	TestTrue(TEXT("newer-version save loads read-only"), Saves->IsReadOnly());
	TestFalse(TEXT("newer-version save is never overwritten"), Saves->Save(Make(1), Slot));
	TestEqual(TEXT("newer-version save still there"), UCDSaveSubsystem::LoadValid(Slot)->SaveVersion, UCDSaveGame::CurrentVersion + 1);

	UCDSaveGame* M = Make(5, 1);
	TestTrue(TEXT("migration runs"), M->Migrate());
	TestTrue(TEXT("migration is repeatable"), M->Migrate() && M->SaveVersion == UCDSaveGame::CurrentVersion && M->GetInt(TEXT("Gold")) == 5);

	Clean();
	return true;
}

#endif
