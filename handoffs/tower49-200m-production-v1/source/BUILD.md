# Reproduce in a new workspace

Use Blender 4.5. Place the Python files from this folder in `work/` under a fresh
workspace, then run each with Blender background mode in this order:

1. `build_tower49.py` - geometry, original 4K HP-to-LP masonry bakes, initial exports.
2. `finish_tower49.py` - map packing, wood/iron, kit/UCX, handhold corrections, UV1.
3. `polish_tower49.py` - natural mineral variation and face-aware UV repair; calls
   `repair_tower49.py` to clean/re-export. Both files must be in `work/`.
4. `fix_tower49_roof.py` - real roof stairwell, edge guard and open approach.
   `export_tower49_door.py` adds the separate closed-door module and collision.
5. `audit_tower49.py` - topology, floor/headroom probes and FBX reimport.
6. `render_tower49_final.py` - final presentation views from the authored mesh.
   `render_tower49_detail.py` adds the focused stair view.

The scripts resolve a sibling `outputs/Tower49_Medieval_200m_v1/` directory. Use
a fresh workspace to avoid overwriting an earlier version. No provider account,
paid generation or Unreal project is used. Python compilation is not an engine
test. Preserve reports and inspect the resulting model; a successful script exit
does not establish visual quality, physics, AI navigation or runtime performance.

The editable master retains the HP tile source, LP architecture and LODs. UV1
is separate from UV0 tiling. PBR texture provenance distinguishes high-poly
geometric bakes from additional authored color/mineral and fitting maps.

