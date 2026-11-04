// #500 point 6: automated tests. Run in the editor: Tools > Session Frontend > Automation, filter "CastleDefender", or from the command line:
//   UnrealEditor-Cmd.exe "<project>.uproject" -ExecCmds="Automation RunTests CastleDefender; Quit" -unattended -nopause -nullrhi
// They test the pure zombie target rule (AZombieBase::ChooseTarget), with no map or Play needed.
#include "Misc/AutomationTest.h"
#include "ZombieBase.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDZombieTargetTest, "CastleDefender.Zombie.ChooseTarget",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCDZombieTargetTest::RunTest(const FString& Parameters)
{
	using FC = AZombieBase::FCandidate;
	const FVector Self(0, 0, 0);
	const FVector Player(5000, 0, 0);
	const float SR = 2500.f, SH = 250.f, FR = 2500.f;

	TestEqual(TEXT("no soldiers or farmers: keep the player"), AZombieBase::ChooseTarget(Self, &Player, {}, {}, SR, SH, FR), INDEX_NONE);

	TArray<FC> Soldiers = { FC{ FVector(1000, 0, 0) }, FC{ FVector(500, 0, 0) } };
	TestEqual(TEXT("nearest soldier in range wins"), AZombieBase::ChooseTarget(Self, &Player, Soldiers, {}, SR, SH, FR), 1);

	Soldiers[1].bDyingOrDead = true;
	TestEqual(TEXT("dying soldier is skipped"), AZombieBase::ChooseTarget(Self, &Player, Soldiers, {}, SR, SH, FR), 0);

	TArray<FC> High = { FC{ FVector(300, 0, 400) } };
	TestEqual(TEXT("soldier 400 cm higher (on the wall) is skipped"), AZombieBase::ChooseTarget(Self, &Player, High, {}, SR, SH, FR), INDEX_NONE);

	TArray<FC> Far = { FC{ FVector(3000, 0, 0) } };
	TestEqual(TEXT("soldier beyond 2500 cm is skipped"), AZombieBase::ChooseTarget(Self, &Player, Far, {}, SR, SH, FR), INDEX_NONE);

	TArray<FC> Farmers = { FC{ FVector(200, 0, 0) } };
	TestEqual(TEXT("nearer farmer beats a soldier (index after soldiers)"), AZombieBase::ChooseTarget(Self, &Player, Soldiers, Farmers, SR, SH, FR), Soldiers.Num());

	const FVector NearPlayer(100, 0, 0);
	TestEqual(TEXT("player nearer than everyone: keep the player"), AZombieBase::ChooseTarget(Self, &NearPlayer, Soldiers, Farmers, SR, SH, FR), INDEX_NONE);

	TestEqual(TEXT("no player (distance 0, as in Blueprint): nothing beats it"), AZombieBase::ChooseTarget(Self, nullptr, Soldiers, Farmers, SR, SH, FR), INDEX_NONE);
	return true;
}

#endif
