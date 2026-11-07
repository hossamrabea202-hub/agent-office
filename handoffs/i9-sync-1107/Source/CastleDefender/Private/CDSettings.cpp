// CDSettings.cpp (2026-11-06): defaults that need code (soft asset paths and the two wasp castes). Everything here can be
// overridden in Project Settings > Game > Castle Defender; DefaultGame.ini then carries the change.
#include "CDSettings.h"

namespace
{
	const TCHAR* WaspDir = TEXT("/Game/CastleDefender/Characters/Enemies/RealmWasp/V2/");
	FSoftObjectPath WaspAsset(const TCHAR* Name) { return FSoftObjectPath(FString(WaspDir) + Name + TEXT(".") + Name); }

	void SkinCaste(FCDWaspCasteSettings& C, const TCHAR* Skin)
	{
		C.BodyMaterial = WaspAsset(*FString::Printf(TEXT("MI_RealmWasp_Body_%s"), Skin));
		C.WingsMaterial = WaspAsset(*FString::Printf(TEXT("MI_RealmWasp_Wings_%s"), Skin));
		C.HairMaterial = WaspAsset(*FString::Printf(TEXT("MI_RealmWasp_Hair_%s"), Skin));
		C.WingBlurMaterial = WaspAsset(*FString::Printf(TEXT("MI_RealmWasp_WingBlur_%s"), Skin));
	}
}

UCDSettings::UCDSettings()
{
	CategoryName = TEXT("Game");

	WaspMesh = WaspAsset(TEXT("SK_RealmWasp"));
	WaspClipHover = WaspAsset(TEXT("A_RealmWasp_Hover"));
	WaspClipFly = WaspAsset(TEXT("A_RealmWasp_Fly"));
	WaspClipDive = WaspAsset(TEXT("A_RealmWasp_Dive"));
	WaspClipSting = WaspAsset(TEXT("A_RealmWasp_Sting"));
	WaspClipDeath = WaspAsset(TEXT("A_RealmWasp_Death"));
	WaspSpitMesh = FSoftObjectPath(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	WaspSlimeScreenMaterial = FSoftObjectPath(TEXT("/Game/CastleDefender/Characters/Enemies/RealmWasp/V2/FX/M_WaspSlimeScreen.M_WaspSlimeScreen"));

	// Drone: the Ember hornet at mesh size. Quick, cowardly, dodges.
	WaspDrone.Scale = 1.f;
	WaspDrone.MaxHP = 110.f;      WaspDrone.HPPerWave = 6.f;
	WaspDrone.StingDamage = 16.f; WaspDrone.XPValue = 8;
	WaspDrone.CruiseSpeed = 1100.f; WaspDrone.HoverSpeed = 500.f; WaspDrone.DiveSpeed = 2300.f; WaspDrone.EscapeSpeed = 1900.f; WaspDrone.Acceleration = 3200.f;
	WaspDrone.PatrolAltitudeMin = 1400.f; WaspDrone.PatrolAltitudeMax = 2000.f;
	WaspDrone.StalkHeight = 800.f; WaspDrone.StalkDistance = 600.f; WaspDrone.StalkPatience = 3.5f;
	WaspDrone.StingReach = 190.f; WaspDrone.HitsPerTarget = 2; WaspDrone.Knockback = 0.f; WaspDrone.bCameraShakeOnSting = false;
	WaspDrone.RetreatFraction = 0.35f; WaspDrone.ReturnFraction = 0.7f; WaspDrone.RetreatRegenPerSecond = 4.f; WaspDrone.RetreatMaxSeconds = 25.f;
	WaspDrone.RetreatAltitude = 3200.f; WaspDrone.RetreatDistance = 3500.f; WaspDrone.MaxRetreats = 2;
	WaspDrone.DodgeChance = 0.45f; WaspDrone.PlayerAimReactSeconds = 0.7f; WaspDrone.BaseHitChance = 0.72f;
	WaspDrone.BuzzPitchHz = 170.f; WaspDrone.BuzzVolume = 0.55f;
	WaspDrone.bCanSpit = true; WaspDrone.SpitDamage = 10.f; WaspDrone.SpitRangeMin = 500.f; WaspDrone.SpitRangeMax = 2200.f; WaspDrone.SpitCooldown = 6.f; WaspDrone.SpitChance = 0.35f;
	WaspDrone.SpitSpeed = 2600.f; WaspDrone.SpitRadius = 18.f; WaspDrone.SlimeSeconds = 6.f; WaspDrone.SlimeSlow = 0.6f;
	WaspDrone.StingInfectChance = 0.3f;
	WaspDrone.NeonColor = FLinearColor(0.15f, 0.85f, 1.f, 1.f);   // teal against the Ember amber
	WaspDrone.SpitMaterial = FSoftObjectPath(TEXT("/Game/CastleDefender/Characters/Enemies/RealmWasp/V2/FX/MI_WaspSpit_Drone.MI_WaspSpit_Drone"));
	WaspDrone.SlimeDecalMaterial = FSoftObjectPath(TEXT("/Game/CastleDefender/Characters/Enemies/RealmWasp/V2/FX/MI_WaspSlimeDecal_Drone.MI_WaspSlimeDecal_Drone"));
	SkinCaste(WaspDrone, TEXT("Ember"));

	// Matriarch: the Blight hornet, semi-colossal. Slow, heavy, cannot dodge, knocks you down, shakes the camera.
	WaspMatriarch.Scale = 3.f;
	WaspMatriarch.MaxHP = 950.f;     WaspMatriarch.HPPerWave = 40.f;
	WaspMatriarch.StingDamage = 42.f; WaspMatriarch.XPValue = 60;
	WaspMatriarch.CruiseSpeed = 850.f; WaspMatriarch.HoverSpeed = 380.f; WaspMatriarch.DiveSpeed = 1700.f; WaspMatriarch.EscapeSpeed = 1300.f; WaspMatriarch.Acceleration = 1500.f;
	WaspMatriarch.PatrolAltitudeMin = 1800.f; WaspMatriarch.PatrolAltitudeMax = 2600.f;
	WaspMatriarch.StalkHeight = 1100.f; WaspMatriarch.StalkDistance = 900.f; WaspMatriarch.StalkPatience = 2.5f;
	WaspMatriarch.StingReach = 420.f; WaspMatriarch.HitsPerTarget = 1; WaspMatriarch.Knockback = 900.f; WaspMatriarch.bCameraShakeOnSting = true;
	WaspMatriarch.RetreatFraction = 0.4f; WaspMatriarch.ReturnFraction = 0.65f; WaspMatriarch.RetreatRegenPerSecond = 14.f; WaspMatriarch.RetreatMaxSeconds = 30.f;
	WaspMatriarch.RetreatAltitude = 3800.f; WaspMatriarch.RetreatDistance = 4200.f; WaspMatriarch.MaxRetreats = 1;
	WaspMatriarch.DodgeChance = 0.f; WaspMatriarch.PlayerAimReactSeconds = 0.f; WaspMatriarch.BaseHitChance = 0.95f;
	WaspMatriarch.BuzzPitchHz = 95.f; WaspMatriarch.BuzzVolume = 0.9f;
	WaspMatriarch.bCanSpit = true; WaspMatriarch.SpitDamage = 28.f; WaspMatriarch.SpitRangeMin = 700.f; WaspMatriarch.SpitRangeMax = 2600.f; WaspMatriarch.SpitCooldown = 4.5f; WaspMatriarch.SpitChance = 0.45f;
	WaspMatriarch.SpitSpeed = 2200.f; WaspMatriarch.SpitRadius = 45.f; WaspMatriarch.SlimeSeconds = 9.f; WaspMatriarch.SlimeSlow = 0.45f;
	WaspMatriarch.StingInfectChance = 0.5f;
	WaspMatriarch.NeonColor = FLinearColor(0.75f, 0.2f, 1.f, 1.f);   // violet against the Blight green
	WaspMatriarch.SpitMaterial = FSoftObjectPath(TEXT("/Game/CastleDefender/Characters/Enemies/RealmWasp/V2/FX/MI_WaspSpit_Matriarch.MI_WaspSpit_Matriarch"));
	WaspMatriarch.SlimeDecalMaterial = FSoftObjectPath(TEXT("/Game/CastleDefender/Characters/Enemies/RealmWasp/V2/FX/MI_WaspSlimeDecal_Matriarch.MI_WaspSlimeDecal_Matriarch"));
	SkinCaste(WaspMatriarch, TEXT("Blight"));
}
