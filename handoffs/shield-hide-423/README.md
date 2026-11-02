# #423 hide the hero's built-in shield while a bought shield is worn (i9, 2026-11-02)

Target: `/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit` EventGraph. Backup: `Tools/PasteRegen_1027/backup_1102/BPC_ShieldKit_before_hideobs.uasset`.

Seen in Play: the hero shows `ObsidianShield` (child of `Shield`) AND `OffHand` (kit shield, `hand_l`) at the same time.

Plan:
- `sk_hideobs.t3d` pastes 5 nodes: GetOwner, pure cast to BP_ThirdPersonCharacter, get `ObsidianShield`, and 2x SceneComponent.SetVisibility.
- `sk_hideobs_wire.py` wires them in:
  - after `vShowShield54` (kit shield shown): ObsidianShield hidden, propagate.
  - after `vHideShield55` (kit shield hidden): ObsidianShield shown, propagate.
  - Each is inserted before whatever followed those nodes. Compile + save.

Blocked: it needs new nodes and editor clicks are denied. Question for i5: is there an existing node chain in BPC_ShieldKit or the hero we could rewire to instead?
