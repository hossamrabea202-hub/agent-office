using UnrealBuildTool;

public class CastleDefender : ModuleRules
{
	public CastleDefender(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "AIModule", "DeveloperSettings" });
	}
}
