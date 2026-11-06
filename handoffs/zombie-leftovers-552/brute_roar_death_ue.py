# Flesh brute leftovers (adjustedfilm, 2026-11-06). Editor idle, not in Play. No paste. Needs #449 stage 2 installed (Anims_Creature clips).
#   py brute_roar_death_ue.py --dry-run | --apply | --revert          Built on the export handoffs/exports/adjustedfilm/brute-449s2/BP_FleshBrute.t3d.txt
# 1. Roar on first sight: once per brute, the first time the player is within 35 m and it is not attacking, it stops, plays CR_Roar_Threat with a real roar (07_Behemoth_Roar_Cue), waits 3 s, then walks on. Think skips its work during the roar.
# 2. Random death: #449's dissolve bypassed every death clip (CX_126 has no input), so the brute froze in its last pose while it dissolved. Now it falls while it dissolves: 50/50 FB_A_Death (CR_Death_Forward) or CR_Death_Side, cut by the 2.2 s lifespan.
# New nodes sit at y >= 60000. --revert removes them and relinks. The script STOPS if a node name is missing.
import sys, os, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
R = '/Game/CastleDefender/Characters/Enemies/FleshBrute'; PATH = R + '/BP_FleshBrute'; ROAR = R + '/Anims_Creature/CR_Roar_Threat'; SIDE = R + '/Anims_Creature/CR_Death_Side'; FWD = R + '/Anims/FB_A_Death'; CUE = '/Game/MonsterRoarsAndGrowls/cues/07_Behemoth_Roar_Cue'; RANGE = 3500.0
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; YMIN = 60000
def say(*a): print('BR552', ' '.join(str(x) for x in a))
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); n = {x.get_name(): x for x in ge.list_all_nodes()}; mine = [x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]
for k in ('CX_1', 'CX_503', 'DsSetCPD', 'CX_17', 'Ps_CX_23', 'PsAnimInst', 'FBGet_CX_126'):
    if k not in n: raise SystemExit('BR552 %s missing; BP_FleshBrute changed, send i5 a fresh export' % k)
if '--revert' in A:
    if mine:
        fr = list(PL.list_connected_pins(BEL.find_execute_pin(next(x for x in mine if x.get_name() and BEL.get_node_pos(x).x == 0 and BEL.get_node_pos(x).y == YMIN))))
        dth = next(x for x in mine if BEL.get_node_pos(x).x == 0 and BEL.get_node_pos(x).y == YMIN + 1000); dsrc = list(PL.list_connected_pins(BEL.find_execute_pin(dth))); ge.remove_nodes(mine)
        say('relink', [PL.try_create_connection(p, BEL.find_execute_pin(n['CX_1'])) for p in fr], [PL.try_create_connection(p, BEL.find_execute_pin(n['DsSetCPD'])) for p in dsrc]); say('compile', BEL.compile_blueprint(bp)); say('saved', E.save_asset(PATH, only_if_is_dirty=False))
    say('DONE revert'); raise SystemExit(0)
miss = [p for p in (ROAR, SIDE) if not E.does_asset_exist(p)]
if miss: raise SystemExit('BR552 missing %s; install #449 stage 2 first' % miss)
if '--apply' not in A: say('WOULD wire. already:', bool(mine), 'cue present', E.does_asset_exist(CUE), 'max y', max(BEL.get_node_pos(x).y for x in ge.list_all_nodes())); raise SystemExit(0)
if mine: say('graph already wired', len(mine)); say('DONE'); raise SystemExit(0)
BEL.compile_blueprint(bp); before = sorted(x.get_name() for x in ge.list_nodes_with_errors())
BEL.add_member_variable(bp, 'Roared', BEL.get_basic_type_by_name('boolean')); BEL.add_member_variable(bp, 'Roaring', BEL.get_basic_type_by_name('boolean')); BEL.compile_blueprint(bp); CLS = bp.generated_class().get_path_name(); pos = [0, YMIN]
def place(x):
    BEL.set_node_pos(x, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300; return x
def ip(x, p):
    r = BEL.find_input_pin(x, p)
    if not r: raise SystemExit('BR552 no input pin %s.%s' % (x.get_name(), p))
    return r
def call(path, **lit):
    x = ge.add_call_function_node(path)
    if not x: raise SystemExit('BR552 no function ' + path)
    place(x)
    for k, v in lit.items(): PL.set_pin_value(ip(x, k), str(v))
    return x
def link(a, pa, b, pb):
    if not PL.try_create_connection(BEL.find_output_pin(a, pa), ip(b, pb)): raise SystemExit('BR552 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def ex(a, b):
    if not PL.try_create_connection(a, BEL.find_execute_pin(b)): raise SystemExit('BR552 exec failed -> ' + b.get_name())
def get(v): return place(ge.add_get_member_variable_node(v))
def setb(v, val):
    x = place(ge.add_set_member_variable_node(v)); PL.set_pin_value(ip(x, v), val); return x
# 1. roar: every path into CX_1 now comes through two branches
src = list(PL.list_connected_pins(BEL.find_execute_pin(n['CX_1']))); PL.break_pin_links(BEL.find_execute_pin(n['CX_1']))
b0 = place(ge.add_branch_node()); link(get('Roaring'), 'Roaring', b0, 'Condition')
for p in src:
    if not PL.try_create_connection(p, BEL.find_execute_pin(b0)): raise SystemExit('BR552 exec failed into the roar branch')
pos[0] = 300; pos[1] = YMIN + 300; pl = call(GS + 'GetPlayerCharacter', PlayerIndex=0); d = call(AC + 'GetDistanceTo'); link(pl, 'ReturnValue', d, 'OtherActor'); lt = call(M + 'Less_DoubleDouble', B=RANGE); link(d, 'ReturnValue', lt, 'A'); n1 = call(M + 'Not_PreBool'); link(get('Roared'), 'Roared', n1, 'A'); n2 = call(M + 'Not_PreBool'); link(get('Attacking'), 'Attacking', n2, 'A'); a1 = call(M + 'BooleanAND'); link(lt, 'ReturnValue', a1, 'A'); link(n1, 'ReturnValue', a1, 'B'); a2 = call(M + 'BooleanAND'); link(a1, 'ReturnValue', a2, 'A'); link(n2, 'ReturnValue', a2, 'B'); b1 = place(ge.add_branch_node()); link(a2, 'ReturnValue', b1, 'Condition'); ex(BEL.find_else_pin(b0), b1); ex(BEL.find_else_pin(b1), n['CX_1'])
pos[0] = 300; pos[1] = YMIN + 600; s1, s2 = setb('Roared', 'true'), setb('Roaring', 'true'); st = call('/Script/Engine.MovementComponent:StopMovementImmediately')
mv = list(PL.list_connected_pins(BEL.find_input_pin(n['CX_17'], 'self')))
if not mv or not PL.try_create_connection(mv[0], ip(st, 'self')): raise SystemExit('BR552 no movement component link from CX_17')
ps = call('/Script/Engine.AnimInstance:PlaySlotAnimationAsDynamicMontage', SlotNodeName='DefaultSlot', BlendInTime=0.2, BlendOutTime=0.3, InPlayRate=1.0, LoopCount=1); PL.set_pin_value(ip(ps, 'Asset'), unreal.load_asset(ROAR).get_path_name()); link(n['PsAnimInst'], 'ReturnValue', ps, 'self')
tail = [s1, s2, st, ps]
if E.does_asset_exist(CUE):
    pos[0] = 300; pos[1] = YMIN + 900; me = call(AC + 'K2_GetActorLocation'); snd = call(GS + 'PlaySoundAtLocation', VolumeMultiplier=1.4, PitchMultiplier=0.9); PL.set_pin_value(ip(snd, 'Sound'), unreal.load_asset(CUE).get_path_name()); link(me, 'ReturnValue', snd, 'Location'); tail.append(snd)
else: say('no cue here: the roar is silent in this project')
pos[0] = 1500; pos[1] = YMIN + 900; dl = call(KS + 'Delay', Duration=3.0); s3 = setb('Roaring', 'false'); b2 = place(ge.add_branch_node()); link(get('Dead'), 'Dead', b2, 'Condition'); go = call(CLS + ':ResumeMove'); tail += [dl, s3, b2]
ex(BEL.find_then_pin(b1), tail[0])
for a_, b_ in zip(tail, tail[1:]): ex(BEL.find_then_pin(a_), b_)
ex(BEL.find_else_pin(b2), go)
# 2. random death
pos[0] = 0; pos[1] = YMIN + 1000; bd = place(ge.add_branch_node()); rb = call(M + 'RandomBool'); link(rb, 'ReturnValue', bd, 'Condition'); dsrc = list(PL.list_connected_pins(BEL.find_execute_pin(n['DsSetCPD']))); PL.break_pin_links(BEL.find_execute_pin(n['DsSetCPD']))
for p in dsrc:
    if not PL.try_create_connection(p, BEL.find_execute_pin(bd)): raise SystemExit('BR552 exec failed into the death branch')
fn = unreal.load_asset(R + '/ABP_FleshBrute').generated_class().get_path_name()
for pin_, clip in ((BEL.find_then_pin(bd), FWD), (BEL.find_else_pin(bd), SIDE)):
    fp = call(fn + ':FB_Play', Loop='false'); PL.set_pin_value(ip(fp, 'Anim'), unreal.load_asset(clip).get_path_name()); link(n['FBGet_CX_126'], 'FBAnim', fp, 'self'); ex(pin_, fp); ex(BEL.find_then_pin(fp), n['DsSetCPD'])
ok = BEL.compile_blueprint(bp); now = sorted(x.get_name() for x in ge.list_nodes_with_errors()); say('compile', ok, 'errors before', len(before), 'after', len(now), 'new', sorted(set(now) - set(before)), 'links into think', len(src), 'into death', len(dsrc))
if set(now) - set(before): raise SystemExit('BR552 NEW compile errors: NOT saved. Close without saving, tell i5')
say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'new nodes', len([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN])); say('DONE')
