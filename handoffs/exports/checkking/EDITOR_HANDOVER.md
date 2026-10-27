# Editor handover (Master offline)

Full guide: [../../master-handover/MASTER_HANDOVER.md](../../master-handover/MASTER_HANDOVER.md) (how to drive the editor, paste recipe, 15 UE 5.3 paste gotchas, systems map, status).
Paste tooling (generators kit2.py/t3dlib.py, nodediff/defdiff/checklive/pastecheck, PIE smoke test): [../../master-handover/tools/](../../master-handover/tools/).

Who drives Unreal: the **Vice Master** seat (or the owner) on the owner's PC; the project is not copied anywhere. Key paste rules for hand-offs:
- Self custom-event calls: `FunctionReference=(MemberName="X",bSelfContext=True)` (MemberParent=own class is silently dropped).
- No literal 0 on pins whose C++ default is non-zero (Add/Subtract/Multiply/Divide B, MakeColor A).
- Impure getters (e.g. GetVectorParameterValue) must be on the exec chain.
- No KismetMathLibrary Ease (dropped): Lerp + Clamp.
- Build on a FRESH export; full-graph replace; diff names against the live Nodes() list after paste.

Status: #36 fixed + verified (self-calls were dropped); #30 mines in, trigger radius fixed 110->190 (#55), hatch after trigger unconfirmed; #32 phase 3 blob splats/pop done; #27/#33/#34 pasted, not seen in Play; Commander bugs #56/#57 open (lead in #57). Own desk tasks #4 #6 #12 #15 #17 #20 #21: not started beyond what's listed.
