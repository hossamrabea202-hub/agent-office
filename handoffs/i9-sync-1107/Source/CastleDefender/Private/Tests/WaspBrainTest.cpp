// Wasp battle system (11-06): the pure rules of ARealmWaspBase, no world needed.
//   UnrealEditor-Cmd.exe "<project>.uproject" -ExecCmds="Automation RunTests CastleDefender.Wasp; Quit" -unattended -nopause -nullrhi
#include "Misc/AutomationTest.h"
#include "RealmWaspBase.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDWaspRetreatTest, "CastleDefender.Wasp.Retreat", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCDWaspRetreatTest::RunTest(const FString& Parameters)
{
	// retreat below the fraction, with retreats left
	TestTrue(TEXT("30 of 100 with 0.35 threshold retreats"), ARealmWaspBase::ShouldRetreat(30.f, 100.f, 0.35f, 0, 2));
	TestFalse(TEXT("40 of 100 with 0.35 threshold fights on"), ARealmWaspBase::ShouldRetreat(40.f, 100.f, 0.35f, 0, 2));
	TestFalse(TEXT("no retreats left: fights to the death"), ARealmWaspBase::ShouldRetreat(10.f, 100.f, 0.35f, 2, 2));
	TestFalse(TEXT("dead wasps do not retreat"), ARealmWaspBase::ShouldRetreat(0.f, 100.f, 0.35f, 0, 2));
	TestFalse(TEXT("bad MaxHP never retreats"), ARealmWaspBase::ShouldRetreat(10.f, 0.f, 0.35f, 0, 2));
	// return when healed or timed out
	TestTrue(TEXT("healed above 0.7 returns"), ARealmWaspBase::ShouldReturn(72.f, 100.f, 0.7f, 3.f, 25.f));
	TestFalse(TEXT("still hurt, still early: stays away"), ARealmWaspBase::ShouldReturn(50.f, 100.f, 0.7f, 3.f, 25.f));
	TestTrue(TEXT("timed out returns even when hurt"), ARealmWaspBase::ShouldReturn(50.f, 100.f, 0.7f, 25.f, 25.f));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDWaspTargetTest, "CastleDefender.Wasp.TargetScore", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCDWaspTargetTest::RunTest(const FString& Parameters)
{
	const float Aggro = 8000.f;
	// kinds: 0 hero, 1 crossbow soldier, 2 soldier, 3 farmer, 4 cannon
	TestTrue(TEXT("a cannon beats the hero (plan: cannons first)"), ARealmWaspBase::ScoreTarget(4, 1000.f, 0, Aggro, 3) > ARealmWaspBase::ScoreTarget(0, 1000.f, 0, Aggro, 3));
	TestTrue(TEXT("hero beats a soldier at equal distance"), ARealmWaspBase::ScoreTarget(0, 1000.f, 0, Aggro, 3) > ARealmWaspBase::ScoreTarget(2, 1000.f, 0, Aggro, 3));
	TestTrue(TEXT("crossbow soldier beats a swordsman"), ARealmWaspBase::ScoreTarget(1, 1000.f, 0, Aggro, 3) > ARealmWaspBase::ScoreTarget(2, 1000.f, 0, Aggro, 3));
	TestTrue(TEXT("a near farmer beats a far hero"), ARealmWaspBase::ScoreTarget(3, 300.f, 0, Aggro, 3) > ARealmWaspBase::ScoreTarget(0, 7900.f, 0, Aggro, 3));
	TestEqual(TEXT("out of aggro range is never a target"), ARealmWaspBase::ScoreTarget(0, 9000.f, 0, Aggro, 3), 0.f);
	TestEqual(TEXT("fully claimed target is never a target"), ARealmWaspBase::ScoreTarget(0, 500.f, 3, Aggro, 3), 0.f);
	TestTrue(TEXT("claims lower the score (the swarm spreads)"), ARealmWaspBase::ScoreTarget(2, 1000.f, 0, Aggro, 3) > ARealmWaspBase::ScoreTarget(2, 1000.f, 1, Aggro, 3));
	TestEqual(TEXT("unknown kind scores nothing"), ARealmWaspBase::ScoreTarget(9, 100.f, 0, Aggro, 3), 0.f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCDWaspLeadTest, "CastleDefender.Wasp.LeadPoint", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCDWaspLeadTest::RunTest(const FString& Parameters)
{
	const FVector From(0, 0, 1000);
	const FVector Still(2000, 0, 0);
	TestEqual(TEXT("a still target is aimed at directly"), ARealmWaspBase::LeadPoint(Still, FVector::ZeroVector, From, 2000.f), Still);
	// target 2000 away, wasp speed 2000 -> about 1 s flight, capped to 0.6 s of lead
	const FVector Led = ARealmWaspBase::LeadPoint(Still, FVector(0, 500, 0), From, 2000.f, 0.6f);
	TestTrue(TEXT("lead is along the target's velocity"), Led.Y > 250.f && Led.Y <= 300.f + KINDA_SMALL_NUMBER);
	TestEqual(TEXT("zero speed does not divide by zero"), ARealmWaspBase::LeadPoint(Still, FVector(0, 500, 0), From, 0.f), Still);
	return true;
}

#endif
