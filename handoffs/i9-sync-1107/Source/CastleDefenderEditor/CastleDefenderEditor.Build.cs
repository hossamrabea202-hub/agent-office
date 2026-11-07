using UnrealBuildTool;

public class CastleDefenderEditor : ModuleRules
{
	public CastleDefenderEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "BlueprintGraph", "AssetRegistry", "AssetTools", "CastleDefender",
			"MeshDescription", "Json", "StaticMeshDescription", "SkeletalMeshDescription", "MeshReductionInterface", "MeshUtilitiesCommon", "AnimationCore" });
	}
}
