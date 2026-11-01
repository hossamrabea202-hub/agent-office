# Weapon Mastery (#416), step 1 (TGA). Editor script, safe to re-run. UE 5.8.
#   py "<repo>/handoffs/skilltree-416/build/setup_tome_ue.py"
# DRY_RUN = True (default): changes NOTHING, only checks every asset this needs and writes setup_tome.txt.
# DRY_RUN = False:
#   1. imports T_SK_Frame + T_SK_Atlas from assets/tga/SkillTome/textures into /Game/CastleDefender/UI/SkillTree/Tome
#   2. creates BPC_SkillTome (ActorComponent) + variables + defaults (skill_data.json) and adds it to the hero as "SkillTome"
# Nothing touches existing materials, textures, decals, the MPC or the level.
import os, json, unreal

DRY_RUN = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'skilltree-416', 'build')
TEX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'tga', 'SkillTome', 'textures'))
DEST = '/Game/CastleDefender/UI/SkillTree/Tome'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_SkillTome'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
NEEDS = ['/Game/CastleDefender/Gameplay/Castle/BP_ArmoryHUD', '/Game/CastleDefender/Gameplay/Castle/BP_SkillTreeHUD', '/Game/CastleDefender/UI/Fonts/Font_Cinzel',
         '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree', '/Game/CastleDefender/UI/Trade/SFX_TradeSwipe', '/Game/CastleDefender/UI/Trade/SFX_TradeBuy',
         '/Game/CastleDefender/UI/Trade/SFX_TradeFail', HERO]
VARS_NEEDED = {HERO: ['Level']}
TEXTURES = ['T_SK_Frame', 'T_SK_Atlas']
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = json.load(open(os.path.join(HERE, 'skill_data.json')))
def var_names(bp, wanted):
    """UE 5.3: Blueprint.new_variables is not readable from Python (#380). Compile, then probe the class default object."""
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have
log = ['DRY_RUN = %s' % DRY_RUN]

missing = [p for p in NEEDS if not EAL.does_asset_exist(p)]
for p in NEEDS: log.append('%-8s %s' % ('ok' if p not in missing else 'MISSING', p))
for n in TEXTURES:
    f = os.path.join(TEX_DIR, n + '.png'); log.append('%-8s %s' % ('ok' if os.path.exists(f) else 'MISSING', f))
def bp_names(path):
    bp = unreal.load_asset(path)
    vars_ = var_names(bp, VARS_NEEDED.get(path, []))
    return vars_

for path, vs in VARS_NEEDED.items():
    if path in missing: continue
    have = bp_names(path)
    for v in vs:
        ok = v in have
        log.append('%-8s %s.%s' % ('ok' if ok else 'MISSING', path.split('/')[-1], v))
        if not ok: missing.append('%s.%s' % (path.split('/')[-1], v))
mpc = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree') if '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree' not in missing else None
if mpc:
    vp = [str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('vector_parameters')]
    for n in ('St', 'RkA', 'RkB', 'Fx'):
        log.append('%-8s MPC_SkillTree.%s' % ('ok' if n in vp else 'MISSING', n))
        if n not in vp: missing.append('MPC_SkillTree.' + n)
log.append('existing BPC_SkillTome: %s' % EAL.does_asset_exist(COMP_DIR + '/' + COMP))

def finish(msg):
    out = 'Weapon Mastery setup (#416)\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_tome.txt'), 'w').write(out); unreal.log(out)

def apply():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    tasks = []
    for n in TEXTURES:
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(TEX_DIR, n + '.png'))
        t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', n)
        t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False)
        tasks.append(t)
    at.import_asset_tasks(tasks)
    tex = {}
    for n in TEXTURES:
        tx = unreal.load_asset('%s/%s' % (DEST, n)); tx.modify()
        tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property('never_stream', True); tx.set_editor_property('srgb', True)
        tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        EAL.save_asset('%s/%s' % (DEST, n)); tex[n] = tx; log.append('texture %s' % n)
    path = COMP_DIR + '/' + COMP
    if EAL.does_asset_exist(path):
        bp = unreal.load_asset(path); log.append('reusing ' + path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        bp = at.create_asset(COMP, COMP_DIR, unreal.Blueprint, f); log.append('created ' + path)
    I, Dd, Bo, Str = (BEL.get_basic_type_by_name(n) for n in ('int', 'real', 'bool', 'string'))
    # UE 5.8: 'real' already comes back as real/double ('double'/'float' silently give int), and EdGraphPinType
    # fields are not exposed to Python, so set_editor_property('pin_sub_category') throws (Master, 2026-11-01)
    assert 'PinSubCategory="double"' in Dd.export_text(), 'real is not double: ' + Dd.export_text()
    LCT = BEL.get_struct_type(unreal.LinearColor.static_struct())
    OBJ, ARR = BEL.get_object_reference_type, BEL.get_array_type
    gen = lambda p: unreal.load_asset(p).generated_class()
    VARS = {n: {'int': I, 'double': Dd, 'bool': Bo}[t] for n, (t, _) in D['vars'].items()}
    VARS.update({'FrameTex': OBJ(unreal.Texture2D), 'AtlasTex': OBJ(unreal.Texture2D),
                 'TabStart': ARR(I), 'TabCount': ARR(I), 'TabSealed': ARR(I), 'TabLearned': ARR(I), 'IRank': ARR(I), 'ICost': ARR(I), 'IState': ARR(I),
                 'INeeds': ARR(Str), 'IPrevName': ARR(Str), 'NameUV': ARR(LCT), 'TitleUV': ARR(LCT), 'TagUV': ARR(LCT), 'D1UV': ARR(LCT), 'GlyphUV': ARR(LCT)})
    have = var_names(bp, list(VARS))
    for n, t in VARS.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
            log.append('  + %s.%s' % (COMP, n))
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    for n, (t, v) in D['vars'].items(): cdo.set_editor_property(n, v)
    dd = D['data']
    for n in ('TabStart', 'TabCount', 'TabSealed', 'TabLearned', 'IRank', 'ICost', 'IState', 'INeeds', 'IPrevName'): cdo.set_editor_property(n, dd[n])
    for n in ('NameUV', 'TitleUV', 'TagUV', 'D1UV', 'GlyphUV'): cdo.set_editor_property(n, [unreal.LinearColor(*q) for q in dd[n]])
    cdo.set_editor_property('FrameTex', tex['T_SK_Frame']); cdo.set_editor_property('AtlasTex', tex['T_SK_Atlas'])
    EAL.save_asset(path)
    hero = unreal.load_asset(HERO)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hero)
    names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
    if 'SkillTome' in names:
        log.append('hero already has SkillTome')
    else:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add component: %s' % fail)
        sds.rename_subobject(h, unreal.Text('SkillTome')); log.append('hero: added SkillTome')
    BEL.compile_blueprint(hero); EAL.save_asset(HERO)
    finish('Next: README step 3 (paste BPC_SkillTome_graph.txt into BPC_SkillTome, Compile, Save).')

if DRY_RUN:
    finish('DRY RUN only. Decision: if nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else
           'STOP: something above is MISSING. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
