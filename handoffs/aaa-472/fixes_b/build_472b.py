# #472 fix B (i5, 2026-11-03): zombie deaths inside ABP_Zombie, hit reacts by side. Run on a fresh BP_Zombie export taken AFTER crowd fix A.
#   python build_472b.py <BP_Zombie export>     -> zombie_b_merged.txt
#  - The 12 death PlayAnimation calls leave AnimBP mode with a pop. They become Montage_Play with the AM_ZDeath_* montages of
#    make_death_montages_ue.py (blend in 0.15 s, no auto blend out: the corpse holds its last pose). Same clip picks, same odds.
#  - CX_97, the last mesh SetPlayRate, goes: it would log in AnimBP mode now.
#  - Stagger: hit from behind (causer > 0.25 behind on the forward axis) plays ZA_Taking_Damage_C, the only clip whose hips jolt forward
#    (hips Y +17 at frame 1, mesh yaw -90, so +Y = actor forward; B, D, E, F jolt -8 to -24). The random front picks no longer pick C.
import json, os, re, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'fixes'))
import build_472 as A
from build_472 import *
HERE = os.path.dirname(os.path.abspath(__file__))      # the star imports overwrite HERE
A.HERE = HERE
ROOT = '/Game/CastleDefender/Characters/Enemies/Zombie/Anim/Death'
DEATHS = ['CX_124', 'CX_126', 'CX_130', 'CX_134', 'CX_138', 'CX_142', 'CX_146', 'CX_150', 'CX_154', 'CX_158', 'CX_162', 'CX_166']
MONT = CLS('AnimMontage'); ANIMI = CLS('AnimInstance')

def clip_of(live, node):
    m = re.search(r'^Begin Object [^\n]*Name="%s".*?^End Object' % node, live, re.S | re.M).group(0)
    return re.search(r'PinName="NewAnimToPlay".*?DefaultObject="[^"]*\.(\w+)"', m).group(1)

def gen(live):
    L = live_links(live); G = Graph(); b = bpkit.B(G, 'zb472'); rw = []
    anim = '%s.%s' % L[('Ps_CX_195', 'self')][0]            # the live GetAnimInstance(Mesh) (pure)
    for i, d in enumerate(DEATHS):
        clip = clip_of(live, d); nm = 'AM_ZDeath_' + clip
        n = b.call(ANIMI, 'Montage_Play', [ob('MontageToPlay', MONT), fl('InPlayRate', default='1.000000'),
                   {'name': 'ReturnValueType', 'cat': 'byte', 'obj': ENUM('EMontagePlayReturnType'), 'default': 'MontageLength'},
                   fl('InTimeToStartMontageAt', default='0.000000'), bo('bStopAllMontages', default='true'), fl('ReturnValue', out=True, default='0.0')], 300 * i, 0, tag='Die')
        pins = G.nodes[-1][3]
        for p in pins:
            if p['name'] == 'MontageToPlay': p['dobj'] = '%s/%s.%s' % (ROOT, nm, nm)
        for s_ in L[(d, 'execute')]: rw.append(R('%s.%s' % s_, n + '.execute', 'was ' + d))
        rw += [R(n + '.then', 'K2Node_CallFunction_ZB76.execute'), {'from': anim, 'to': n + '.self'}]
    # BP_ZombieWallBreaker started a PlayAnimation in its BeginPlay, so it is in single-node mode and a montage would not show. force=false: a no-op on
    # the zombies already in AnimBP mode, a re-init only where the mode really changes.
    sm = b.call(SKEL, 'SetAnimationMode', [{'name': 'InAnimationMode', 'cat': 'byte', 'obj': ENUM('EAnimationMode'), 'default': 'AnimationBlueprint'},
                bo('bForceInitAnimScriptInstance', default='false')], 0, 200, tag='BackToABP')
    animnode = anim.split('.')[0]
    meshsrc = '%s.%s' % L[(animnode, 'self')][0]
    rw += [R('K2Node_CallFunction_ZB73.then', sm + '.execute'), {'from': meshsrc, 'to': sm + '.self'}]
    # killed by a cannonball: ragdoll + impulse instead of a death clip (Ragdoll profile, all bodies; seen flying in Simulate on a probe). CX_528 is the live ClassIsChildOf(causer, BP_Cannonball).
    ifball = b.branch(None, 300, 600, tag='IfBallKill')
    prof = b.call(CLS('PrimitiveComponent'), 'SetCollisionProfileName', [N('InCollisionProfileName', default='Ragdoll'), bo('bUpdateOverlaps', default='true')], 600, 600, tag='RagProfile')
    phys = b.call(SKEL, 'SetAllBodiesSimulatePhysics', [bo('bNewSimulate', default='true')], 900, 600, tag='RagBodies')
    imp = b.call(CLS('PrimitiveComponent'), 'AddRadialImpulse', [V('Origin'), fl('Radius', default='800.0'), fl('Strength', default='900.0'),
                 {'name': 'Falloff', 'cat': 'byte', 'obj': ENUM('ERadialImpulseFalloff'), 'default': 'RIF_Linear'}, bo('bVelChange', default='true')], 1200, 600, tag='RagImpulse')
    cl0 = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 900, 800, pure=True, const=True, tag='BallLoc')
    org = b.v2('Subtract_VectorVector', (cl0, 'ReturnValue'), None, 1100, 800, db='0, 0, 120')
    G.link(org[0], org[1], imp, 'Origin')
    G.link(ifball, 'then', prof, 'execute'); G.link(prof, 'then', phys, 'execute'); G.link(phys, 'then', imp, 'execute')
    rw += [R(sm + '.then', ifball + '.execute'), R(ifball + '.else', 'CX_123.execute'), R(imp + '.then', 'K2Node_CallFunction_ZB76.execute'),
           {'from': 'CX_528.ReturnValue', 'to': ifball + '.Condition'}, {'from': meshsrc, 'to': prof + '.self'}, {'from': meshsrc, 'to': phys + '.self'}, {'from': meshsrc, 'to': imp + '.self'},
           {'from': 'K2Node_Event_ZB60.DamageCauser', 'to': cl0 + '.self'}]
    # BP_SoldierSword CX_173 (15 % of engagements) calls PlayAnimation on a zombie's mesh: single-node mode, and nothing brought it back since the montage
    # conversion, so that zombie stays frozen in A_Attack's last pose. Safety net on every resume: same force = false call, no-op in AnimBP mode.
    sm2 = b.call(SKEL, 'SetAnimationMode', [{'name': 'InAnimationMode', 'cat': 'byte', 'obj': ENUM('EAnimationMode'), 'default': 'AnimationBlueprint'},
                 bo('bForceInitAnimScriptInstance', default='false')], 0, 250, tag='ResumeABP')
    rw += [R('K2Node_IfThenElse_ZB10.else', sm2 + '.execute'), R(sm2 + '.then', 'CX_300.execute'), {'from': '%s.%s' % L[(animnode, 'self')][0], 'to': sm2 + '.self'}]
    # hit from behind: IsValid(causer) first, Blueprint's AND does not short-circuit
    causer = 'K2Node_Event_ZB60.DamageCauser'
    iv = b.valid(None, 0, 400); ifc = b.branch(iv, 300, 300, tag='IfCauser')
    cl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 0, 600, pure=True, const=True, tag='CauserLoc')
    me = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 0, 750, pure=True, const=True, tag='MyLoc')
    fw = b.call(ACT, 'GetActorForwardVector', [V('ReturnValue', out=True)], 0, 900, pure=True, const=True, tag='MyFwd')
    to = b.v2('Subtract_VectorVector', (cl, 'ReturnValue'), (me, 'ReturnValue'), 300, 650)
    nrm = b.math('Normal', [(V('A'), to), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 550, 650)
    dot = b.math('Dot_VectorVector', [(V('A'), (fw, 'ReturnValue')), (V('B'), nrm)], D('ReturnValue', out=True), 800, 750)
    ifb = b.branch(b.dcmp('Less_DoubleDouble', dot, None, 1050, 750, db='-0.25'), 1300, 300, tag='IfBehind')
    G.link(ifc, 'then', ifb, 'execute')
    for s_ in L[('Ps_CX_209', 'execute')]: rw.append(R('%s.%s' % s_, 'Ps_CX_205.execute', 'C is the from-behind clip now'))
    rw += [R('CX_194.else', ifc + '.execute'), R(ifc + '.else', 'CX_200.execute'), R(ifb + '.then', 'Ps_CX_209.execute'), R(ifb + '.else', 'CX_200.execute'),
           {'from': causer, 'to': iv[0] + '.Object'}, {'from': causer, 'to': cl + '.self'}]
    open(os.path.join(HERE, 'zombie_b_paste.txt'), 'w', newline='\r\n').write(G.render()); print('zombie_b_paste.txt', len(G.nodes), 'nodes')
    json.dump({'blueprint': 'BP_Zombie', 'note': '#472 fix B: death montages, hit from behind', 'pastes': ['zombie_b_paste.txt'], 'rewires': rw},
              open(os.path.join(HERE, 'zombie_b_manifest.json'), 'w'), indent=1)

if __name__ == '__main__':
    z = A.to_graph(sys.argv[1])
    gen(open(z, encoding='utf-8', errors='replace', newline='').read().replace('\r\n', '\n'))
    A.build(z, 'zombie_b_manifest.json', DEATHS + ['CX_97'], 'zombie_b_merged.txt')
    print('OK: paste zombie_b_merged.txt into BP_Zombie')
