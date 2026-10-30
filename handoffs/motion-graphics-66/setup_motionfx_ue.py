# Motion graphics #66 / #139 / #140 / #86 / #141, step 1 (checkking, 2026-10-30). Editor script, safe to re-run.
#   py "<repo>/handoffs/motion-graphics-66/setup_motionfx_ue.py"
# 1. imports the 6 HUD textures from assets/checkking/RevealMG/textures into /Game/CastleDefender/UI/Reveal
#    (UI group, no mips, clamp, never stream): the two 8x8 flipbook atlases and the 4 effect textures
# 2. creates BPC_MotionFX (ActorComponent) with its variables and adds it to the hero as "MotionFX"
# Needs M_HintCard (/Game/CastleDefender/UI/Hints): if it is missing, run handoffs/pickup-reveals-66/make_M_HintCard.py first.
# Writes setup_motionfx.txt next to itself.
import os, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'motion-graphics-66')
TEX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'checkking', 'RevealMG', 'textures'))
DEST = '/Game/CastleDefender/UI/Reveal'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_MotionFX'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
HINT = '/Game/CastleDefender/UI/Hints/M_HintCard'
TEXTURES = ['T_Reveal_Book_Atlas', 'T_Reveal_Bag_Atlas', 'T_FX_RevealRays', 'T_FX_Sparkles', 'T_FX_ToxinVignette', 'T_FX_ToxinVeins']
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
log = []
if not EAL.does_asset_exist(HINT):
    raise RuntimeError('M_HintCard is missing: run handoffs/pickup-reveals-66/make_M_HintCard.py first')

# ---------------------------------------------------------------- 1. textures
tasks = []
for n in TEXTURES:
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(TEX_DIR, n + '.png'))
    t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', n)
    t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False)
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for n in TEXTURES:
    tx = unreal.load_asset('%s/%s' % (DEST, n))
    tx.modify()
    tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tx.set_editor_property('never_stream', True)
    tx.set_editor_property('srgb', True)
    tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    EAL.save_asset('%s/%s' % (DEST, n)); log.append('texture %s %s' % (n, tx.blueprint_get_size_x()))

# ---------------------------------------------------------------- 2. component + variables
path = COMP_DIR + '/' + COMP
if EAL.does_asset_exist(path):
    bp = unreal.load_asset(path); log.append('reusing ' + path)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(COMP, COMP_DIR, unreal.Blueprint, f); log.append('created ' + path)
Dd = BEL.get_basic_type_by_name('real'); Dd.set_editor_property('pin_sub_category', 'double')
Bo = BEL.get_basic_type_by_name('bool')
VARS = {'BookT0': Dd, 'BagT0': Dd, 'BookOpened': Bo, 'BagOpened': Bo, 'BookOpenNow': Bo, 'BagOpenNow': Bo,
        'CardMID': BEL.get_object_reference_type(unreal.MaterialInstanceDynamic),
        # #141 infection look
        'InfT0': Dd, 'InfLevel': Dd}
have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
for n, t in VARS.items():
    if n not in have:
        if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
        log.append('  + %s.%s' % (COMP, n))
BEL.compile_blueprint(bp); EAL.save_asset(path)

hero = unreal.load_asset(HERO)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
handles = sds.k2_gather_subobject_data_for_blueprint(hero)
names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
if 'MotionFX' in names:
    log.append('hero already has MotionFX')
else:
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero))
    if not fail.is_empty(): raise RuntimeError('add component: %s' % fail)
    sds.rename_subobject(h, unreal.Text('MotionFX')); log.append('hero: added MotionFX')
BEL.compile_blueprint(hero); EAL.save_asset(HERO)

out = 'Motion graphics setup\n' + '\n'.join(log) + '\nNext: paste BPC_MotionFX_graph.txt into BPC_MotionFX EventGraph (README step 3).'
open(os.path.join(HERE, 'setup_motionfx.txt'), 'w').write(out)
unreal.log(out)
