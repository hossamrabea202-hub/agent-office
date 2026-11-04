using UnrealBuildTool;

public class CastleDefenderTarget : TargetRules
{
	public CastleDefenderTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V5;            // pinned (review); raise on purpose with an engine upgrade
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5;  // pinned; if 5.8 offers Unreal5_8 and the build is clean, move to it
		ExtraModuleNames.Add("CastleDefender");
	}
}
