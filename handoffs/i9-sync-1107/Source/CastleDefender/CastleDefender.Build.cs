using UnrealBuildTool;

public class CastleDefender : ModuleRules
{
	public CastleDefender(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "AIModule", "DeveloperSettings", "NavigationSystem", "UMG", "InputCore", "EnhancedInput", "Slate", "SlateCore", "MediaAssets", "AudioExtensions", "AudioMixer", "SignalProcessing", "Niagara", "ProceduralMeshComponent" });
	}
}
