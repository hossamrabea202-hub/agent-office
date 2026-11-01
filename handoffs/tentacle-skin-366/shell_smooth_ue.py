# Tentacle bio-shield stretch fix (i5 core, 2026-11-01, owner Alien's screenshot 180755): the jelly shell's cell net smears
# in a horizontal band on the lower trunk. Cause: JellyShellVS builds the around-the-spine angle from the tangent of the
# NEAREST spine segment; at each joint the tangent jumps, so the angle jumps -> a smeared/stepped band where the spine
# bends (worst at the root bend). Fix: tangent interpolated between joint tangents (continuous), in a COPY of the master.
#   py "<repo>/handoffs/tentacle-skin-366/shell_smooth_ue.py" [--dry-run]     build M_TentacleJellyShell_Smooth
#   py ".../shell_smooth_ue.py" --swap [--dry-run]                             re-parent every MI_TentacleJellyShell_* to it
#   py ".../shell_smooth_ue.py" --revert                                       back to M_TentacleJellyShell (backup json)
import json, os, sys, unreal
A = sys.argv[1:]
DRY, SWAP, REVERT = '--dry-run' in A, '--swap' in A, '--revert' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(os.path.expanduser('~'), 'agent-office', 'handoffs', 'tentacle-skin-366')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
SRC, DST = '/Game/CastleDefender/VFX/JellyBubble/M_TentacleJellyShell', '/Game/CastleDefender/VFX/JellyBubble/M_TentacleJellyShell_Smooth'
BACKUP = os.path.join(HERE, 'shell_smooth_backup.json')
log = ['#366 shell smooth %s%s' % ('--swap' if SWAP else '--revert' if REVERT else 'build', ' (DRY RUN)' if DRY else '')]
OLD_IF = '    if (d2 < best) { best = d2; s = lerp(SV[i], SV[i + 1], tt); Q = q; Tg = normalize(ab); }'
NEW_IF = '    if (d2 < best) { best = d2; s = lerp(SV[i], SV[i + 1], tt); Q = q; Tg = normalize(ab); bi = i; btt = saturate(tt); }'
OLD_U = 'float3 U = normalize(cross(float3(0.0, 1.0, 0.0), Tg));'
SMOOTH = '''// i5 2026-11-01: tangent interpolated between joint tangents, so the around-angle has no jump at segment joints.
{
    float3 t0 = normalize(B[bi + 1] - B[bi]);
    float3 tp = (bi > 0) ? normalize(B[bi] - B[bi - 1]) : t0;
    float3 tn = (bi < 12) ? normalize(B[bi + 2] - B[bi + 1]) : t0;
    Tg = normalize(lerp(normalize(tp + t0), normalize(t0 + tn), btt));
}
'''


def shell_mis():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    return sorted(str(a.package_name) for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant'))
                  if str(a.asset_name).startswith('MI_TentacleJellyShell'))


def vs_node(m):
    todo, seen = [MEL.get_material_property_input_node(m, p) for p in (unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET, unreal.MaterialProperty.MP_BASE_COLOR,
                                                                       unreal.MaterialProperty.MP_EMISSIVE_COLOR, unreal.MaterialProperty.MP_OPACITY)], set()
    while todo:
        e = todo.pop()
        if e is None or e.get_name() in seen: continue
        seen.add(e.get_name())
        if isinstance(e, unreal.MaterialExpressionCustom) and e.get_editor_property('code').lstrip().startswith('// JellyShellVS'): return e
        todo += [x for x in MEL.get_inputs_for_material_expression(m, e) if x]
    return None


if not (SWAP or REVERT):
    m = unreal.load_asset(SRC); n = vs_node(m)
    code = n.get_editor_property('code') if n else ''
    ok = OLD_IF in code and OLD_U in code and 'float best = 1e20;' in code
    log.append('JellyShellVS found: %s, patch points found: %s' % (bool(n), ok))
    if ok and not DRY:
        swapped = [p for p in shell_mis() if unreal.load_asset(p).get_editor_property('parent').get_path_name().startswith(DST)]
        if swapped: raise RuntimeError('MIs use the smooth copy (%s): --revert before rebuilding' % swapped)
        if EAL.does_asset_exist(DST): EAL.delete_asset(DST)
        EAL.duplicate_asset(SRC, DST); EAL.save_asset(DST)
        m2 = unreal.load_asset(DST); n2 = vs_node(m2)          # in a live session the fresh copy's graph can be unreadable until reloaded
        if n2 is None: MEL.recompile_material(m2); n2 = vs_node(m2)
        if n2 is None: raise RuntimeError('JellyShellVS not found on the copy %s: rerun' % DST)
        c = n2.get_editor_property('code')
        c = c.replace('float best = 1e20;', 'int bi = 0; float btt = 0.0; float best = 1e20;', 1).replace(OLD_IF, NEW_IF, 1).replace(OLD_U, SMOOTH + OLD_U, 1)
        n2.set_editor_property('code', c); n2.set_editor_property('description', 'JellyShellVS smooth (i5)')
        MEL.recompile_material(m2); EAL.save_asset(DST); log.append('built ' + DST)
else:
    back = json.load(open(BACKUP)) if os.path.exists(BACKUP) else {}
    for p in shell_mis():
        mi = unreal.load_asset(p); cur = mi.get_editor_property('parent').get_path_name().split('.')[0]
        if SWAP and cur == SRC:
            log.append('%s -> smooth' % p.split('/')[-1])
            if not DRY: back[p] = cur; MEL.set_material_instance_parent(mi, unreal.load_asset(DST)); EAL.save_asset(p)
        elif REVERT and p in back:
            log.append('%s -> %s' % (p.split('/')[-1], back[p].split('/')[-1]))
            if not DRY: MEL.set_material_instance_parent(mi, unreal.load_asset(back[p])); EAL.save_asset(p); back.pop(p)
        else:
            log.append('%s parent %s (skipped)' % (p.split('/')[-1], cur.split('/')[-1]))
    if not DRY: json.dump(back, open(BACKUP, 'w'), indent=1)
out = '\n'.join(log); unreal.log(out); print(out)
