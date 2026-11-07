#include "CDBakeHordeCommandlet.h"
#include "CDHordeAnimData.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "Animation/AttributesRuntime.h"
#include "Animation/Skeleton.h"
#include "AnimationRuntime.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "BoneContainer.h"
#include "BonePose.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "IMeshReductionInterfaces.h"
#include "IMeshReductionManagerModule.h"
#include "Materials/MaterialInterface.h"
#include "MeshDescription.h"
#include "MeshReductionSettings.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "OverlappingCorners.h"
#include "SkeletalMeshAttributes.h"
#include "StaticMeshAttributes.h"
#include "StaticMeshCompiler.h"
#include "StaticMeshOperations.h"
#include "TextureCompiler.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

DEFINE_LOG_CATEGORY_STATIC(LogCDBake, Log, All);

namespace CDBake
{
	static const TCHAR* Folder = TEXT("/Game/CastleDefender/Horde");
	static const TCHAR* ZombieFolder = TEXT("/Game/CastleDefender/Characters/Enemies/Zombie/");

	struct FClipSpec { const TCHAR* Role; const TCHAR* Path; bool bLoop; };
	// Role order = texture order. Paths relative to ZombieFolder. All verified on SK_Zombie_Skeleton (inspection 2026-11-05).
	static const FClipSpec Clips[] = {
		{ TEXT("Walk"),   TEXT("AnimsPack/ZA_Walk_A"),   true },
		{ TEXT("Walk"),   TEXT("AnimsPack/ZA_Walk_B"),   true },
		{ TEXT("Walk"),   TEXT("AnimsPack/ZA_Walk_C"),   true },
		{ TEXT("Run"),    TEXT("Anims/A_Run"),           true },
		{ TEXT("Run"),    TEXT("AnimsPack/ZA_Run_A"),    true },
		{ TEXT("Attack"), TEXT("AnimsPack/ZA_Attack_A"), true },
		{ TEXT("Attack"), TEXT("AnimsPack/ZA_Attack_B"), true },
		{ TEXT("Attack"), TEXT("AnimsPack/ZA_Attack_D"), true },
		{ TEXT("Attack"), TEXT("Anims/A_Attack"),        true },
		{ TEXT("Death"),  TEXT("Anims/A_Death"),         false },
		{ TEXT("Death"),  TEXT("AnimsPack/ZA_Burst_B"),  false },
		{ TEXT("Death"),  TEXT("AnimsPack/ZA_Burst_D"),  false },
		{ TEXT("Idle"),   TEXT("AnimsPack/ZA_Idle_A"),   true },
	};

	struct FWeights4 { int32 Bone[4] = { 0, 0, 0, 0 }; float W[4] = { 1.f, 0.f, 0.f, 0.f }; };

	template <typename T>
	static T* GetOrCreate(const FString& Name, bool& bOutNew)
	{
		const FString PkgName = FString(Folder) / Name;
		const FString ObjPath = PkgName + TEXT(".") + Name;
		if (T* Existing = LoadObject<T>(nullptr, *ObjPath, nullptr, LOAD_NoWarn | LOAD_Quiet)) { bOutNew = false; return Existing; }
		UPackage* Pkg = CreatePackage(*PkgName);
		Pkg->FullyLoad();
		bOutNew = true;
		return NewObject<T>(Pkg, *Name, RF_Public | RF_Standalone);
	}

	static bool Save(UObject* Asset, bool bNew)
	{
		UPackage* Pkg = Asset->GetOutermost();
		Pkg->MarkPackageDirty();
		if (bNew) { FAssetRegistryModule::AssetCreated(Asset); }
		const FString File = FPackageName::LongPackageNameToFilename(Pkg->GetName(), FPackageName::GetAssetPackageExtension());
		FSavePackageArgs Args;
		Args.TopLevelFlags = RF_Public | RF_Standalone;
		Args.Error = GError;
		const bool bOk = UPackage::SavePackage(Pkg, Asset, *File, Args);
		UE_LOG(LogCDBake, Display, TEXT("%s %s"), bOk ? TEXT("saved") : TEXT("SAVE FAILED"), *File);
		return bOk;
	}

	static FWeights4 Top4(TArray<TPair<int32, float>>& In)
	{
		In.Sort([](const TPair<int32, float>& A, const TPair<int32, float>& B) { return A.Value > B.Value; });
		FWeights4 R;
		float Sum = 0.f;
		for (int32 k = 0; k < 4; ++k)
		{
			R.Bone[k] = k < In.Num() ? In[k].Key : 0;
			R.W[k] = k < In.Num() ? FMath::Max(0.f, In[k].Value) : 0.f;
			Sum += R.W[k];
		}
		if (Sum <= KINDA_SMALL_NUMBER) { R = FWeights4(); return R; }
		for (float& W : R.W) { W /= Sum; }
		return R;
	}

	// Per-vertex weights of a skeletal mesh description (empty when it has none).
	static void ReadWeights(const FMeshDescription& MD, TMap<int32, FWeights4>& Out)
	{
		Out.Reset();
		FSkeletalMeshConstAttributes SA(MD);
		FSkinWeightsVertexAttributesConstRef SW = SA.GetVertexSkinWeights();
		if (!SW.IsValid()) { return; }
		for (const FVertexID V : MD.Vertices().GetElementIDs())
		{
			const FVertexBoneWeightsConst BW = SW.Get(V);
			TArray<TPair<int32, float>> L;
			for (int32 k = 0; k < BW.Num(); ++k) { L.Add({ int32(BW[k].GetBoneIndex()), BW[k].GetWeight() }); }
			Out.Add(V.GetValue(), Top4(L));
		}
	}
}

int32 UCDBakeHordeCommandlet::Main(const FString& Params)
{
	using namespace CDBake;
	const bool bDry = FParse::Param(*Params, TEXT("dry"));
	FString MeshPath = FString(ZombieFolder) + TEXT("SK_Zombie");
	FParse::Value(*Params, TEXT("mesh="), MeshPath);
	float FPS = 30.f;
	FParse::Value(*Params, TEXT("fps="), FPS);
	FPS = FMath::Clamp(FPS, 5.f, 60.f);

	USkeletalMesh* Skel = LoadObject<USkeletalMesh>(nullptr, *(MeshPath + TEXT(".") + FPackageName::GetShortName(MeshPath)));
	if (!Skel || !Skel->GetSkeleton()) { UE_LOG(LogCDBake, Error, TEXT("no skeletal mesh / skeleton at %s"), *MeshPath); return 1; }
	const FReferenceSkeleton& Ref = Skel->GetRefSkeleton();
	const int32 NB = Ref.GetNum();
	UE_LOG(LogCDBake, Display, TEXT("mesh %s: %d bones, %d LODs"), *Skel->GetName(), NB, Skel->GetLODNum());

	// ---------------- bone texture
	TArray<FTransform> RefCS;
	FAnimationRuntime::FillUpComponentSpaceTransforms(Ref, Ref.GetRefBonePose(), RefCS);
	TArray<FBoneIndexType> Req;
	for (int32 b = 0; b < NB; ++b) { Req.Add(FBoneIndexType(b)); }
	FBoneContainer BC(Req, UE::Anim::FCurveFilterSettings(), *Skel);

	TArray<FCDHordeClip> OutClips;
	TArray<FFloat16Color> Pixels;
	const int32 W = 2 * NB;
	int32 Row = 0, BadScale = 0;
	for (const FClipSpec& Spec : Clips)
	{
		const FString P = FString(ZombieFolder) + Spec.Path;
		UAnimSequence* Seq = LoadObject<UAnimSequence>(nullptr, *(P + TEXT(".") + FPackageName::GetShortName(P)));
		if (!Seq) { UE_LOG(LogCDBake, Error, TEXT("missing clip %s"), *P); return 2; }
		if (Seq->GetSkeleton() != Skel->GetSkeleton()) { UE_LOG(LogCDBake, Error, TEXT("clip %s is on another skeleton"), *P); return 2; }
		const float Len = Seq->GetPlayLength();
		const int32 NF = FMath::Max(1, FMath::RoundToInt(Len * FPS));
		FCDHordeClip C;
		C.Name = FName(FString::Printf(TEXT("%s_%s"), Spec.Role, *Seq->GetName()));
		C.StartFrame = Row;
		C.NumFrames = NF;
		C.FPS = FPS;
		C.bLoop = Spec.bLoop;
		OutClips.Add(C);
		Pixels.AddZeroed(NF * W);
		for (int32 f = 0; f < NF; ++f)
		{
			FMemMark Mark(FMemStack::Get());   // FCompactPose / FBlendedCurve allocate on the mem stack
			FCompactPose Pose;
			Pose.SetBoneContainer(&BC);
			FBlendedCurve Curve;
			Curve.InitFrom(BC);
			UE::Anim::FStackAttributeContainer Attr;
			FAnimationPoseData PD(Pose, Curve, Attr);
			Seq->GetAnimationPose(PD, FAnimExtractContext(double(FMath::Min(f / FPS, Len))));

			TArray<FTransform> Local = Ref.GetRefBonePose();
			for (const FCompactPoseBoneIndex CI : Pose.ForEachBoneIndex())
			{
				const int32 MB = BC.MakeMeshPoseIndex(CI).GetInt();
				if (MB >= 0 && MB < NB) { Local[MB] = Pose[CI]; }
			}
			// contract: root X/Y held at the reference pose
			const FVector R0 = Ref.GetRefBonePose()[0].GetTranslation();
			Local[0].SetTranslation(FVector(R0.X, R0.Y, Local[0].GetTranslation().Z));
			TArray<FTransform> CS;
			FAnimationRuntime::FillUpComponentSpaceTransforms(Ref, Local, CS);
			for (int32 b = 0; b < NB; ++b)
			{
				const FTransform D = RefCS[b].Inverse() * CS[b];
				if (!D.GetScale3D().Equals(FVector::OneVector, 0.01)) { ++BadScale; }
				const FQuat Q = D.GetRotation().GetNormalized();
				const FVector T = D.GetTranslation();
				FFloat16Color& PQ = Pixels[(Row + f) * W + 2 * b];
				FFloat16Color& PT = Pixels[(Row + f) * W + 2 * b + 1];
				PQ = FFloat16Color(FLinearColor(float(Q.X), float(Q.Y), float(Q.Z), float(Q.W)));
				PT = FFloat16Color(FLinearColor(float(T.X), float(T.Y), float(T.Z), 1.f));
			}
		}
		UE_LOG(LogCDBake, Display, TEXT("clip %-28s rows %4d..%4d (%d frames, %.2f s, loop %d)"), *C.Name.ToString(), Row, Row + NF - 1, NF, Len, C.bLoop);
		Row += NF;
	}
	const int32 TotalFrames = Row;
	if (TotalFrames > 16384 || W > 16384) { UE_LOG(LogCDBake, Error, TEXT("texture %dx%d too big"), W, TotalFrames); return 3; }
	if (BadScale > 0) { UE_LOG(LogCDBake, Warning, TEXT("%d bone deltas have scale != 1 (the contract ignores scale)"), BadScale); }

	// ---------------- crowd mesh LODs
	IMeshReduction* Reducer = FModuleManager::Get().LoadModuleChecked<IMeshReductionManagerModule>("MeshReductionInterface").GetStaticMeshReductionInterface();
	FMeshDescription Src0;
	if (!Skel->CloneMeshDescription(0, Src0)) { UE_LOG(LogCDBake, Error, TEXT("LOD0 has no mesh description")); return 4; }
	TMap<int32, FWeights4> SrcW;
	ReadWeights(Src0, SrcW);
	if (SrcW.Num() == 0) { UE_LOG(LogCDBake, Error, TEXT("LOD0 has no skin weights")); return 4; }
	TArray<FVector3f> SrcPos;
	TArray<int32> SrcId;
	{
		const TVertexAttributesConstRef<FVector3f> P = Src0.GetVertexPositions();
		for (const FVertexID V : Src0.Vertices().GetElementIDs()) { SrcPos.Add(P[V]); SrcId.Add(V.GetValue()); }
	}

	struct FLodPlan { int32 SkelLOD; float Pct; };
	const FLodPlan Plan[2] = { { 1, 0.30f }, { 3, 0.10f } };
	TArray<FMeshDescription> Lods;
	Lods.SetNum(2);
	for (int32 l = 0; l < 2; ++l)
	{
		FMeshDescription& MD = Lods[l];
		TMap<int32, FWeights4> LW;
		const int32 SL = FMath::Min(Plan[l].SkelLOD, Skel->GetLODNum() - 1);
		FString How;
		if (Skel->HasMeshDescription(SL) && Skel->CloneMeshDescription(SL, MD)) { ReadWeights(MD, LW); How = FString::Printf(TEXT("skeletal LOD%d"), SL); }
		if (LW.Num() == 0)
		{
			MD = FMeshDescription();
			FStaticMeshAttributes(MD).Register();
			FOverlappingCorners OC;
			FStaticMeshOperations::FindOverlappingCorners(OC, Src0, THRESH_POINTS_ARE_SAME);
			FMeshReductionSettings S;
			S.PercentTriangles = Plan[l].Pct;
			S.PercentVertices = Plan[l].Pct;
			S.TerminationCriterion = EStaticMeshReductionTerimationCriterion::Triangles;
			float Dev = 0.f;
			Reducer->ReduceMeshDescription(MD, Dev, Src0, OC, S);
			How = FString::Printf(TEXT("LOD0 reduced to %.0f%% (deviation %.2f cm), weights from the nearest LOD0 vertex"), Plan[l].Pct * 100.f, Dev);
		}
		FStaticMeshAttributes Attr(MD);
		Attr.Register();
		TVertexInstanceAttributesRef<FVector2f> UVs = Attr.GetVertexInstanceUVs();
		if (UVs.GetNumChannels() < 5) { UVs.SetNumChannels(5); }
		const TVertexAttributesConstRef<FVector3f> Pos = MD.GetVertexPositions();
		int32 MaxBone = 0;
		for (const FVertexInstanceID VI : MD.VertexInstances().GetElementIDs())
		{
			const FVertexID V = MD.GetVertexInstanceVertex(VI);
			const FWeights4* Wt = LW.Find(V.GetValue());
			FWeights4 Near;
			if (!Wt)
			{
				const FVector3f P = Pos[V];
				float Best = TNumericLimits<float>::Max();
				int32 BestI = 0;
				for (int32 s = 0; s < SrcPos.Num(); ++s)
				{
					const float D = FVector3f::DistSquared(P, SrcPos[s]);
					if (D < Best) { Best = D; BestI = s; }
				}
				Near = SrcW.FindRef(SrcId[BestI]);
				Wt = &Near;
			}
			for (int32 k = 0; k < 4; ++k) { MaxBone = FMath::Max(MaxBone, Wt->Bone[k]); }
			UVs.Set(VI, 1, FVector2f(float(Wt->Bone[0]), float(Wt->Bone[1])));
			UVs.Set(VI, 2, FVector2f(float(Wt->Bone[2]), float(Wt->Bone[3])));
			UVs.Set(VI, 3, FVector2f(Wt->W[0], Wt->W[1]));
			UVs.Set(VI, 4, FVector2f(Wt->W[2], Wt->W[3]));
		}
		if (MaxBone >= NB) { UE_LOG(LogCDBake, Error, TEXT("LOD%d uses bone %d but the mesh has %d"), l, MaxBone, NB); return 5; }
		UE_LOG(LogCDBake, Display, TEXT("crowd LOD%d: %d vertices, %d triangles (%s)"), l, MD.Vertices().Num(), MD.Triangles().Num(), *How);
	}

	if (bDry) { UE_LOG(LogCDBake, Display, TEXT("dry run: %d clips, %d frames, texture %dx%d. Nothing saved."), OutClips.Num(), TotalFrames, W, TotalFrames); return 0; }

	// ---------------- texture
	bool bNewTex = false;
	UTexture2D* Tex = GetOrCreate<UTexture2D>(TEXT("T_HordeZombie_Bones"), bNewTex);
	Tex->PreEditChange(nullptr);
	Tex->Source.Init(W, TotalFrames, 1, 1, TSF_RGBA16F, reinterpret_cast<const uint8*>(Pixels.GetData()));
	Tex->SRGB = false;
	Tex->CompressionSettings = TC_HDR;
	Tex->MipGenSettings = TMGS_NoMipmaps;
	Tex->Filter = TF_Nearest;
	Tex->NeverStream = true;
	Tex->LODGroup = TEXTUREGROUP_16BitData;
	Tex->AddressX = TA_Clamp;
	Tex->AddressY = TA_Clamp;
	Tex->PostEditChange();
	FTextureCompilingManager::Get().FinishAllCompilation();

	// ---------------- static mesh
	bool bNewMesh = false;
	UStaticMesh* SM = GetOrCreate<UStaticMesh>(TEXT("SM_HordeZombie"), bNewMesh);
	SM->PreEditChange(nullptr);
	SM->GetStaticMaterials().Reset();
	TArray<UMaterialInterface*> SlotMats;
	{
		FStaticMeshAttributes A0(Lods[0]);
		const TPolygonGroupAttributesConstRef<FName> Slots = A0.GetPolygonGroupMaterialSlotNames();
		for (const FPolygonGroupID G : Lods[0].PolygonGroups().GetElementIDs())
		{
			const FName Slot = Slots[G];
			UMaterialInterface* M = nullptr;
			for (const FSkeletalMaterial& SkM : Skel->GetMaterials())
			{
				if (SkM.ImportedMaterialSlotName == Slot || SkM.MaterialSlotName == Slot) { M = SkM.MaterialInterface; break; }
			}
			SM->GetStaticMaterials().Add(FStaticMaterial(M, Slot, Slot));
			SlotMats.Add(M);
		}
	}
	SM->SetNumSourceModels(2);
	for (int32 l = 0; l < 2; ++l)
	{
		FStaticMeshSourceModel& SrcModel = SM->GetSourceModel(l);
		SrcModel.BuildSettings.bRecomputeNormals = false;
		SrcModel.BuildSettings.bRecomputeTangents = false;
		SrcModel.BuildSettings.bGenerateLightmapUVs = false;
		SrcModel.BuildSettings.bUseFullPrecisionUVs = true;
		SrcModel.BuildSettings.bRemoveDegenerates = false;
		SrcModel.ReductionSettings = FMeshReductionSettings();   // no further reduction: the LODs are already built
		SrcModel.ScreenSize.Default = l == 0 ? 1.0f : 0.12f;
		SM->CreateMeshDescription(l, MoveTemp(Lods[l]));
		SM->CommitMeshDescription(l);
	}
	SM->SetAutoComputeLODScreenSize(false);
	SM->GetNaniteSettings().bEnabled = false;
	SM->SetPositiveBoundsExtension(FVector(130.f, 130.f, 40.f));   // swinging arms, lying deaths, melt spread
	SM->SetNegativeBoundsExtension(FVector(130.f, 130.f, 10.f));
	SM->Build(false);
	SM->PostEditChange();
	FStaticMeshCompilingManager::Get().FinishAllCompilation();

	// ---------------- data asset
	bool bNewData = false;
	UCDHordeAnimData* Data = GetOrCreate<UCDHordeAnimData>(TEXT("DA_HordeZombie"), bNewData);
	Data->Mesh = SM;
	Data->BoneTexture = Tex;
	Data->NumBones = NB;
	Data->TotalFrames = TotalFrames;
	Data->Clips = OutClips;
	Data->FormatVersion = UCDHordeAnimData::CurrentFormatVersion;
	bool bKeepMats = Data->Materials.Num() == SlotMats.Num();
	for (const TObjectPtr<UMaterialInterface>& M : Data->Materials) { bKeepMats &= M != nullptr; }
	if (!bKeepMats)
	{
		// placeholders (static pose, no animation) until the crowd materials from i5's script are assigned
		Data->Materials.Reset();
		for (UMaterialInterface* M : SlotMats) { Data->Materials.Add(M); }
		UE_LOG(LogCDBake, Warning, TEXT("crowd materials not set yet: using the zombie's own materials as placeholders (instances will not animate)"));
	}

	FString Why;
	const bool bValid = Data->IsValidContract(Why);
	UE_LOG(LogCDBake, Display, TEXT("contract v%d check: %s %s"), Data->FormatVersion, bValid ? TEXT("OK") : TEXT("FAILED:"), *Why);
	if (!bValid) { return 6; }

	bool bAll = Save(Tex, bNewTex);
	bAll &= Save(SM, bNewMesh);
	bAll &= Save(Data, bNewData);
	UE_LOG(LogCDBake, Display, TEXT("bake done: %d bones, %d clips, %d frames, texture %dx%d, %s"), NB, OutClips.Num(), TotalFrames, W, TotalFrames, bAll ? TEXT("all saved") : TEXT("SAVE ERRORS"));
	return bAll ? 0 : 7;
}
