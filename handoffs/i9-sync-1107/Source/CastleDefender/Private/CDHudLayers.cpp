// CDHudLayers.cpp - REVIEW DRAFT rev 3, 2026-11-06 (see CDHudLayers.h)
#include "CDHudLayers.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CoreMisc.h"

namespace CDHudLayers
{
	static FString GNativeLayers;   // default "": nothing changes until a level is switched on
	static FAutoConsoleVariableRef CVarLayers(TEXT("cd.Hud.NativeLayers"), GNativeLayers,
		TEXT("HUD levels drawn by generated C++ instead of their Blueprint graph: \"\" none (default), \"*\" all, or a comma list of Blueprint names (BP_ControlsHUD,...)."));

	// parsed once per change of the cvar text, not every frame
	static FString GParsedFrom = TEXT("\x01");
	static TSet<FName> GParsed;
	static bool GAll = false;

	struct FLayerState { bool bNative = false; int32 Epoch = 0; };
	static TMap<FName, FLayerState> GLayers;

	// rev 3 (review P1-8): draw trace. UseNativeLayer is called exactly once per level per draw by its switch, on BOTH paths
	// (Blueprint and native) and also when a native child runs its parent's event, so it sees the real parent-to-child order.
	// cd.Hud.TraceDraws 1: once a second, log the last complete frame's sequence and flag any level drawn more or less than
	// once, compared with the set of levels seen in the first traced frame.
	static int32 GTrace = 0;
	static FAutoConsoleVariableRef CVarTrace(TEXT("cd.Hud.TraceDraws"), GTrace, TEXT("1 = log the HUD level draw order once a second and flag levels drawn twice / not at all (parent-call parity check)."));
	static uint64 GTraceFrame = 0;
	static TArray<FName> GThisFrame, GLastFrame, GExpected;
	static double GLastLog = 0.0;
	static void Trace(FName Layer)
	{
		if (!GTrace) { GExpected.Reset(); return; }
		if (GFrameCounter != GTraceFrame)
		{
			GLastFrame = MoveTemp(GThisFrame); GThisFrame.Reset(); GTraceFrame = GFrameCounter;
			if (GExpected.Num() == 0 && GLastFrame.Num() > 0) { GExpected = GLastFrame; }
			const double Now = FPlatformTime::Seconds();
			if (GLastFrame.Num() > 0 && Now - GLastLog > 1.0)
			{
				GLastLog = Now;
				FString Seq; TMap<FName, int32> Count;
				for (const FName& N : GLastFrame) { Seq += N.ToString() + TEXT(" > "); ++Count.FindOrAdd(N); }
				FString Bad;
				for (const FName& N : GExpected) { const int32 C = Count.FindRef(N); if (C != 1) { Bad += FString::Printf(TEXT(" %s x%d"), *N.ToString(), C); } }
				for (const TPair<FName, int32>& KV : Count) { if (!GExpected.Contains(KV.Key)) { Bad += FString::Printf(TEXT(" %s (unexpected) x%d"), *KV.Key.ToString(), KV.Value); } }
				if (Bad.IsEmpty()) { UE_LOG(LogTemp, Display, TEXT("cd.Hud.TraceDraws OK: %s"), *Seq); }
				else { UE_LOG(LogTemp, Error, TEXT("cd.Hud.TraceDraws MISMATCH:%s | order: %s"), *Bad, *Seq); }
			}
		}
		GThisFrame.Add(Layer);
	}

	static bool Wanted(FName Layer)
	{
		if (GNativeLayers != GParsedFrom)
		{
			GParsedFrom = GNativeLayers;
			GParsed.Reset();
			GAll = GNativeLayers.TrimStartAndEnd() == TEXT("*");
			TArray<FString> Parts;
			GNativeLayers.ParseIntoArray(Parts, TEXT(","));
			for (FString& P : Parts) { P.TrimStartAndEndInline(); if (!P.IsEmpty() && P != TEXT("*")) { GParsed.Add(FName(*P)); } }
		}
		return GAll || GParsed.Contains(Layer);   // FName compare is case-insensitive
	}
}

bool UCDHudLayers::UseNativeLayer(FName Layer)
{
	using namespace CDHudLayers;
	Trace(Layer);
	const bool bNow = Wanted(Layer);
	FLayerState& S = GLayers.FindOrAdd(Layer);
	if (S.bNative != bNow) { S.bNative = bNow; ++S.Epoch; }   // a switch in either direction starts a new epoch
	return bNow;
}

int32 UCDHudLayers::GetLayerEpoch(FName Layer)
{
	const CDHudLayers::FLayerState* S = CDHudLayers::GLayers.Find(Layer);
	return S ? S->Epoch : 0;
}

bool UCDHudLayers::IsLayerNativeNow(FName Layer)
{
	const CDHudLayers::FLayerState* S = CDHudLayers::GLayers.Find(Layer);
	return S && S->bNative && CDHudLayers::Wanted(Layer);
}
