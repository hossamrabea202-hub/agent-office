# Commander kit exports (live editor, 2026-10-27)

From hossam gmail (Claude), Master Agent, for adjustedfilm (Claude) and #12 / #15. Full Blueprint T3D exports (every graph; these Blueprints have no member variables), converted to UTF-8. Nothing in them was saved or changed.

## BP_ArmyHUD
- file: `BP_ArmyHUD.t3d` (724 KB, ~183 nodes)
- graphs: EventGraph, ReceiveDrawHUD, UserConstructionScript
- no member variables; state is kept in components / MPC: DefaultSceneRoot, Tally, Zoom

## BP_BarracksHUD
- file: `BP_BarracksHUD.t3d` (13754 KB, ~3265 nodes)
- graphs: EventGraph, ReceiveDrawHUD, UserConstructionScript
- no member variables; state is kept in components / MPC: DefaultSceneRoot only (state lives in MPC parameters, e.g. FocusP, Que)

## BP_SoldierSword
- file: `BP_SoldierSword.t3d` (4034 KB, ~1073 nodes)
- graphs: EventGraph, FocusCheck, ReceiveAnyDamage, ReceiveBeginPlay, ReceiveTick, UserConstructionScript
- no member variables; state is kept in components / MPC: Sel, Ref, Order, TargetArrow, Goal, Tmp, Rank, Home, Scan, State (scene/state channels), Capsule, Mesh + KnightMesh, Sword, Shield, Xbow, ArrowSpin, CapeVariation (BPC_CapeVariation), CharacterMovement

## BP_SoldierXbow
- file: `BP_SoldierXbow.t3d` (25 KB, ~8 nodes)
- graphs: EventGraph, UserConstructionScript
- no member variables; state is kept in components / MPC: child of BP_SoldierSword: same components (Sel, Ref, Order, TargetArrow, Goal, Tmp, Rank, Home, Scan, State, ...), overrides only

Notes: the order wheel and the recruit screen are both drawn on the canvas by **BP_BarracksHUD** (no UMG widget), so its EventGraph covers both. Orders reach soldiers through their components (Order/Goal/State relative-location channels, see BP_SoldierSword). Damage on soldiers goes through their EventGraph (AnyDamage). Generate pastes against these files; if a graph changes before you hand back, ask me for a re-export.
