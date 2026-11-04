using UnrealBuildTool;

public class CastleDefenderEditorTarget : TargetRules
{
	public CastleDefenderEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.AddRange(new string[] { "CastleDefender", "CastleDefenderEditor" });
	}
}
