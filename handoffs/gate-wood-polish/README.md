# Main gate material polish (i5, 2026-11-02)

**Materials and textures only.** These are untouched:
- `BP_GateBreachLeaf`, `BP_CastleMainGate`, the lever BP
- the skeletal meshes and their animations
- triggers, collision and the GateDamage / claw-scratch / mud logic

## What was wrong (measured)
- **Iron straps / ledgers / Z-braces** (procedural, in `M_GateBreach_Scratched`'s custom shader): near-black 0.035 linear
  **and** fully metallic. That renders as black plastic (KNOWLEDGE_LOG 10-30). The `IronColor` / `IronARM` inputs were
  wired into the shader but never sampled.
- **Oak** (`T_GateOak_ORM`): roughness almost flat, std 0.022 (rule: ≥ 0.05), so the boards read as plastic.
- **Leaf slot 1** used StarterContent `M_Metal_Steel`: 128 sRGB, half of it in-between metallic.

## What changed
- `M_GateBreach_Scratched`: the iron block of the custom node only.
  - **Oxide:** blackened mill-scale oxide, dielectric, 0.037 linear (about 54 sRGB), matte-satin roughness 0.72–0.9,
    mottled by the forge-scale texture.
  - **Bare metal:** 0.5 linear, metallic 1, roughness 0.35, only on rubbed corners.
  - **Rust:** unchanged.
  - **Backup:** `M_GateBreach_Scratched_BACKUP_polish`. The patch is always rebuilt from that backup, so it can't stack.
- `MI_GateBreach_Scratched_L` (backup `_BACKUP_polish`):
  - `WoodORM` → `T_GateOak_ORM_v2`: grain roughness 0.69–0.87, std 0.055.
  - `IronColor` / `IronARM` → the forged iron v2 textures.
- New in `Props/GateBreach/Polish/`:
  - `T_GateOak_ORM_v2`, `T_GateIron_D_v2`, `T_GateIron_ARM_v2` (`pbr_check` OK)
  - `M_GateIron_Forged`
- **Placed gate leaves (level):** slot-1 override → `M_GateIron_Forged`.

## Apply on the Master (i9)
1. Unzip into the project root, with the editor closed. It brings `Props/GateBreach/*` and `Props/GateBreach/Polish/*`.
2. Open the editor and run `py apply_gate_polish_ue.py --leaves`. This sets slot 1 on the 2 placed `BP_GateBreachLeaf`.
   **Save the map.**
3. **Play-check:**
   - open and close the gate (lever)
   - breach damage stages / claw scratches
   - mud on the outside face
   - both leaves animate as before
4. **Undo:** `py apply_gate_polish_ue.py --revert`. It restores the shader code, the MI params and the slot-1 override.

## Shots
`shots/before_leaf.png` vs `shots/after_leaf.png`: leaf-only render, side key light, same fixed exposure.
