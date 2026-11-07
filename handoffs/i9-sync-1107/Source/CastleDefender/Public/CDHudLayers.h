// CDHudLayers.h - REVIEW DRAFT rev 4, 2026-11-06. The per-layer switch between a HUD level's Blueprint draw graph and its generated
// C++ (UCDHudGen::Draw_<Level>, CDHudGen.h). The editor tool InsertNativeLayerSwitch puts, at the start of each level's
// Event ReceiveDrawHUD:   Branch( UseNativeLayer("<Level>") )   True -> UCDHudGen::Draw_<Level>(self, SizeX, SizeY)
//                                                                False -> the original graph, untouched.
// cd.Hud.NativeLayers: ""  = every level runs its Blueprint graph (DEFAULT: integrating changes nothing until switched on)
//                      "*" = every level runs its generated C++
//                      "BP_ControlsHUD,BP_ArmyHUD" = only those (A/B one level at a time, live, no rebuild)
// rev 2 (review P1): every change of a level's native/Blueprint choice increments that level's EPOCH.
//   - pending native Delay continuations carry the epoch they were scheduled in and are dropped if it changed
//     (or the level is no longer native), so a native continuation never runs while the Blueprint graph is active;
//   - the native state (ubergraph-frame equivalent, rule R3) resets when the epoch changes: a re-enabled native level starts
//     from a zeroed frame, like a freshly spawned HUD. The Blueprint graph's own frame is separate and never touched.
//   Known limit: Blueprint latent actions (Delay) already pending in the Blueprint graph when a level is switched TO native
//   still finish in the Blueprint graph (the engine owns them). Switch levels while no menu is mid-animation for A/B tests.
// rev 4 (second review): what switching does and does NOT promise. Two modes, named explicitly:
//   PARITY TEST MODE - the only mode used to claim "native == Blueprint". Set cd.Hud.NativeLayers BEFORE the HUD exists (start PIE
//     with the value, or switch, then restart the level), so both paths start from the same freshly spawned state, then compare
//     with cd.Hud.TraceDraws and screenshots / logged values.
//   LIVE FALLBACK MODE - switching a level while playing (e.g. turning a misbehaving native level back to Blueprint). Safe: no
//     native continuation runs while Blueprint is active, nothing dangles, no crash. NOT state-equivalent: the native frame
//     starts zeroed, the Blueprint frame keeps its own values, so an open menu may jump (e.g. a fade restarts, a selected tab
//     resets) on the first frames after the switch. No state is synchronised between the two frames.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CDHudLayers.generated.h"

UCLASS()
class CASTLEDEFENDER_API UCDHudLayers : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Castle Defender|HUD")
	static bool UseNativeLayer(FName Layer);

	// Current epoch of a level (starts at 0, +1 every time UseNativeLayer's answer for it changes).
	static int32 GetLayerEpoch(FName Layer);

	// For pending native continuations (Delay): is the level native right now, by the live cvar, and was it native at its last
	// draw? No trace entry, no epoch change (only the draw switch moves epochs).
	static bool IsLayerNativeNow(FName Layer);
};
