// Horde (owner, 2026-11-05): baked crowd data for far zombies. Made by the editor commandlet -run=CDBakeHorde.
// The crowd material plays the clips on the GPU from per-instance custom data, so the CPU only moves instances.
//
// ===== BAKE / MATERIAL CONTRACT, version 1 (FormatVersion). The bake tool writes it, IsValidContract() checks it at load. =====
// Bones
//   - Bone index b = the index in the SOURCE skeletal mesh's reference skeleton (SK_Zombie RefSkeleton), 0..NumBones-1. Not the Skeleton
//     asset's index, not a render-section BoneMap index.
// Bone texture (BoneTexture)
//   - Format RGBA16F (TSF_RGBA16F), no compression (TC_HDR), no mips, no sRGB, nearest filter, never streamed.
//   - Width = 2 * NumBones, Height = TotalFrames. Read only with Texture2D.Load(int3(x, y, 0)) (integer texel addressing, no sampler).
//   - Row y = one baked frame. Texel (2b, y) = rotation quaternion (x, y, z, w), unit length. Texel (2b+1, y) = translation (x, y, z) in cm, w = 1.
//   - Each (rotation, translation) is the bone's DELTA transform in mesh component space:  D = Inverse(RefCS[b]) * AnimCS[b]
//     (Unreal order: apply the left one first). So a reference-pose vertex v moves to  D(v) = q * v * q^-1 + t.  Scale is not stored (must be 1).
//   - The root bone's X/Y translation is held at the reference pose (no root motion slides out of the instance).
// Frames and clips
//   - Every clip is sampled at its FPS (30) from t = 0 to t = PlayLength inclusive of the first frame: NumFrames = max(1, round(PlayLength * FPS)).
//     Frame k is at time min(k / FPS, PlayLength). Clips sit back to back: StartFrame of clip i+1 = StartFrame + NumFrames of clip i.
//   - Name = "<Role>_<source asset name>", Role one of Walk, Run, Attack, Death, Idle. Walk, Attack and Death must have at least one clip.
//   - Death clips: bLoop = false (hold the last frame). All others loop.
// Crowd mesh (Mesh)
//   - Built from the skeletal mesh's own vertices in reference pose, mesh component space, same material slots in the same order.
//   - UV0 = the original texture UV. UV1 = (bone0, bone1), UV2 = (bone2, bone3) as whole numbers (mesh bone index, exact in half float up to 2048).
//     UV3 = (weight0, weight1), UV4 = (weight2, weight3): the 4 largest influences, renormalised to sum 1, sorted largest first; unused = (0, weight 0).
//   - Bounds extended so baked poses (arms, lying deaths, melt spread) are never culled.
// Per-instance custom data (6 floats, written by UCDHordeSubsystem)
//   [0] clip StartFrame   [1] clip NumFrames   [2] world time the clip started (s, already offset for a random phase)
//   [3] FPS, negative = no loop (hold the last frame)   [4] world time the melt started (0 = not melting)   [5] tint (0 normal, 1 brute)
// Material frame rule (vertex shader)
//   f = max(Time - C2, 0) * |C3|;  loop: f = fmod(f, C1), next = fmod(floor(f) + 1, C1);  hold: f = min(f, C1 - 1), next = min(floor(f) + 1, C1 - 1)
//   rows r0 = C0 + floor(f), r1 = C0 + next, blend a = frac(f): position = lerp(skin(r0), skin(r1), a), skin = sum over 4 influences of w * D_b(v).
//   Time = the material Time node = world time in seconds (UWorld::GetTimeSeconds), so C2 and C4 use the same clock.
//   melt m = C4 > 0 ? smoothstep(saturate((Time - C4) / 1.6)) : 0, applied after skinning in mesh space (Z up, origin at the feet).
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CDHordeAnimData.generated.h"

class UStaticMesh;
class UTexture2D;
class UMaterialInterface;

USTRUCT(BlueprintType)
struct FCDHordeClip
{
	GENERATED_BODY()

	// Role prefix + source name, for example Walk_ZA_Walk_A. Roles: Walk, Run, Attack, Death, Idle.
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName Name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 StartFrame = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 NumFrames = 1;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	float FPS = 30.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	bool bLoop = true;

	float Length() const { return NumFrames / FMath::Max(1.f, FPS); }
};

UCLASS(BlueprintType)
class CASTLEDEFENDER_API UCDHordeAnimData : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	TObjectPtr<UStaticMesh> Mesh;

	// One per mesh material slot (crowd versions of the zombie's own materials).
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	TArray<TObjectPtr<UMaterialInterface>> Materials;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	TObjectPtr<UTexture2D> BoneTexture;

	// Deferred decal for the wet pool a melted zombie leaves behind.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	TObjectPtr<UMaterialInterface> MeltPoolDecal;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	int32 NumBones = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	int32 TotalFrames = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	TArray<FCDHordeClip> Clips;

	static constexpr int32 CurrentFormatVersion = 1;

	// The contract version the bake tool wrote. The runtime refuses data of another version.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Horde")
	int32 FormatVersion = 0;

	// Checks the contract above against the assets (texture size, clip table, roles). Fills OutError with the first problem.
	bool IsValidContract(FString& OutError) const;

	// Indices of the clips whose name starts with Role + "_".
	void ClipsForRole(const TCHAR* Role, TArray<int32>& Out) const
	{
		Out.Reset();
		const FString Prefix = FString(Role) + TEXT("_");
		for (int32 i = 0; i < Clips.Num(); ++i)
		{
			if (Clips[i].Name.ToString().StartsWith(Prefix)) { Out.Add(i); }
		}
	}
};
