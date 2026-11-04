using UnrealBuildTool;

public class CastleDefenderTarget : TargetRules
{
	public CastleDefenderTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("CastleDefender");
	}
}
