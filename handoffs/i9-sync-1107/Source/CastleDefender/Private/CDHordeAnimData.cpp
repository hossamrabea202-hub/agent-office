#include "CDHordeAnimData.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"

bool UCDHordeAnimData::IsValidContract(FString& OutError) const
{
	if (FormatVersion != CurrentFormatVersion) { OutError = FString::Printf(TEXT("format version %d, runtime expects %d (re-run the bake)"), FormatVersion, CurrentFormatVersion); return false; }
	if (!Mesh) { OutError = TEXT("no mesh"); return false; }
	if (!BoneTexture) { OutError = TEXT("no bone texture"); return false; }
	if (NumBones <= 0 || TotalFrames <= 0) { OutError = FString::Printf(TEXT("bones %d frames %d"), NumBones, TotalFrames); return false; }
	int32 SX = BoneTexture->GetSizeX(), SY = BoneTexture->GetSizeY();
	bool bFormatOk = BoneTexture->GetPixelFormat() == PF_FloatRGBA;
#if WITH_EDITORONLY_DATA
	if (SX == 0 || SY == 0)   // no platform data yet (commandlets never build it): check the source instead
	{
		SX = int32(BoneTexture->Source.GetSizeX());
		SY = int32(BoneTexture->Source.GetSizeY());
		bFormatOk = BoneTexture->Source.GetFormat() == TSF_RGBA16F && BoneTexture->CompressionSettings == TC_HDR;
	}
#endif
	if (SX != 2 * NumBones || SY != TotalFrames)
	{
		OutError = FString::Printf(TEXT("bone texture %dx%d, contract needs %dx%d"), SX, SY, 2 * NumBones, TotalFrames);
		return false;
	}
	if (!bFormatOk) { OutError = TEXT("bone texture is not RGBA16F"); return false; }
	if (Materials.Num() != Mesh->GetStaticMaterials().Num()) { OutError = TEXT("material count differs from the mesh's slots"); return false; }

	int32 Next = 0;
	bool bWalk = false, bAttack = false, bDeath = false;
	for (const FCDHordeClip& C : Clips)
	{
		if (C.StartFrame != Next || C.NumFrames < 1 || C.FPS <= 0.f) { OutError = FString::Printf(TEXT("clip %s: start %d (expected %d), frames %d"), *C.Name.ToString(), C.StartFrame, Next, C.NumFrames); return false; }
		Next += C.NumFrames;
		const FString N = C.Name.ToString();
		if (N.StartsWith(TEXT("Walk_"))) { bWalk = true; }
		else if (N.StartsWith(TEXT("Attack_"))) { bAttack = true; }
		else if (N.StartsWith(TEXT("Death_"))) { bDeath = true; if (C.bLoop) { OutError = N + TEXT(" must not loop"); return false; } }
		else if (!N.StartsWith(TEXT("Run_")) && !N.StartsWith(TEXT("Idle_"))) { OutError = N + TEXT(": unknown role"); return false; }
	}
	if (Next != TotalFrames) { OutError = FString::Printf(TEXT("clips cover %d frames, texture has %d"), Next, TotalFrames); return false; }
	if (!bWalk || !bAttack || !bDeath) { OutError = TEXT("needs at least one Walk_, Attack_ and Death_ clip"); return false; }
	return true;
}
