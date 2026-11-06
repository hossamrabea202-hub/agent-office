# #509 step 2 (i5 checkking, 2026-11-05): wind sway (World Position Offset) off at distance, INDUSTRY_SECRETS 2 (VSM) + 4.4:
# swaying WPO re-renders virtual shadow pages every frame; past a distance nobody sees the sway, so stop it there.
#   py wpo_audit509_ue.py                 DRY RUN: lists every swaying thing in the open level + foliage types, writes wpo_report509.txt
#   py wpo_audit509_ue.py --apply         sets the distance where it is 0 (= never off) or larger than the target; saves the
#                                         foliage type assets it changed; the level actors are changed in the level (save the level)
# Targets (cm): trees 5000, bushes / ground plants / grass 2500, cloth (banners, flags, tents) 4000, anything else that sways 3000.
# Never touched: things that already stop sooner, and WPO that is NOT wind (tentacles, realm flesh, water, zombies, VFX):
# those are gameplay motion, and switching them off at distance would freeze them visibly.
import sys, unreal
A = sys.argv[1:]; APPLY = '--apply' in A
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): print('PIE RUNNING: abort'); raise SystemExit
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); MEL = unreal.MaterialEditingLibrary
NOT_WIND = ('tentacle', 'realm', 'flesh', 'corrupt', 'water', 'zombie', 'ocean', 'river', 'jelly', 'blob', 'fx', 'niagara', 'bubble', 'portal', 'lava', 'fire', 'flame')
_wpo = {}


def base(m):
    while isinstance(m, unreal.MaterialInstance): m = m.get_editor_property('parent')
    return m


def uses_wpo(m):
    b = base(m)
    if not b: return False
    k = b.get_path_name()
    if k not in _wpo:
        try: _wpo[k] = MEL.get_material_property_input_node(b, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is not None
        except Exception: _wpo[k] = False
    return _wpo[k]


def kind(key):
    if any(w in key for w in NOT_WIND): return None
    if any(w in key for w in ('tree', 'pine', 'oak', 'birch', 'spruce', 'fir', 'beech', 'trunk', 'canopy')): return ('tree', 5000.0)
    if any(w in key for w in ('banner', 'flag', 'cloth', 'tent', 'canvas', 'awning', 'curtain', 'rope')): return ('cloth', 4000.0)
    if any(w in key for w in ('grass', 'bush', 'shrub', 'fern', 'flower', 'flora', 'daisy', 'poppy', 'foxglove', 'weed', 'reed', 'plant', 'ivy', 'moss', 'clover', 'foliage')): return ('plant', 2500.0)
    return ('other', 3000.0)


rows, changed = [], 0
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        if not isinstance(c, unreal.MeshComponent): continue
        try: mats = [c.get_material(i) for i in range(c.get_num_materials())]
        except Exception: continue
        mats = [m for m in mats if m]
        if not any(uses_wpo(m) for m in mats): continue
        sm = c.get_editor_property('static_mesh') if isinstance(c, unreal.StaticMeshComponent) else None
        key = ' '.join([a.get_actor_label(), a.get_class().get_name(), sm.get_name() if sm else '', c.get_name()] + [m.get_name() for m in mats] + [base(m).get_name() for m in mats if base(m)]).lower()
        k = kind(key)
        if k and isinstance(c, unreal.SkeletalMeshComponent) and k[0] != 'cloth': k = None      # characters: not wind
        try: cur = c.get_editor_property('world_position_offset_disable_distance')
        except Exception: cur = None
        n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
        act = '-'
        if k and cur is not None and (cur == 0 or cur > k[1]):
            act = 'set %d' % k[1]
            if APPLY: c.modify(); c.set_editor_property('world_position_offset_disable_distance', int(k[1])); changed += 1
        rows.append('%-6s %-6s cur %6s  inst %6d  %s | %s | %s' % (k[0] if k else 'NOWIND', act, cur, n, a.get_actor_label()[:40], sm.get_name() if sm else c.get_class().get_name(), base(mats[0]).get_name() if mats else ''))
# foliage types (the foliage paint tool and procedural foliage read their own setting)
ft_rows = []
for ad in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(unreal.TopLevelAssetPath('/Script/Foliage', 'FoliageType_InstancedStaticMesh'), True):
    if not str(ad.package_name).startswith('/Game/'): continue
    ft = ad.get_asset(); sm = ft.get_editor_property('mesh')
    if not sm: continue
    mats = [s.get_editor_property('material_interface') for s in sm.get_editor_property('static_materials')]
    ov = ft.get_editor_property('override_materials') or []
    mats = [m for m in list(ov) + mats if m]
    if not any(uses_wpo(m) for m in mats): continue
    k = kind((str(ad.asset_name) + ' ' + sm.get_name()).lower())
    try: cur = ft.get_editor_property('world_position_offset_disable_distance')
    except Exception: cur = None
    act = '-'
    if k and cur is not None and (cur == 0 or cur > k[1]):
        act = 'set %d' % k[1]
        if APPLY:
            ft.set_editor_property('world_position_offset_disable_distance', int(k[1]))
            unreal.EditorAssetLibrary.save_asset(str(ad.package_name), only_if_is_dirty=False); changed += 1
    ft_rows.append('%-6s %-6s cur %6s  %s' % (k[0] if k else 'NOWIND', act, cur, ad.package_name))
out = ['WPO audit: %d swaying level components, %d swaying foliage types, %s' % (len(rows), len(ft_rows), ('%d CHANGED' % changed) if APPLY else 'dry run')]
out += ['', '# level components'] + sorted(rows) + ['', '# foliage types'] + sorted(ft_rows)
open('C:/Users/hossam.rabea/agent-office/handoffs/castle-props-509/wpo_report509.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(out[0]); print('to change:', sum(1 for r in rows + ft_rows if ' set ' in r))
