# #472 fix C (i5, 2026-11-03): significance + hit feel on BP_Zombie. Run on a fresh export taken AFTER fix A and fix B.
#   python build_472c.py <BP_Zombie export>   -> zombie_c_merged.txt
#  - Significance, at the top of Think (dist = distance to the player): under 30 m every Think, 30-60 m every 2nd, beyond 60 m every 4th (1 x a second).
#    Beyond 30 m AND not rendered: CharacterMovement ticks at 10 Hz and the actor at 4 Hz. Rendered zombies always keep full rate.
#  - Hit-stop: a blow of at least 25 % of MaxHP freezes the victim for 60 ms (CustomTimeDilation 0.02, restored by a timer).
#  - Brute flinch: brutes had no reaction at all (CX_531's then is empty). Additive montage AM_ZFlinch_Front / Back, at most one a second,
#    Montage_Play with bStopAllMontages = false, because a brute's crawl is itself a looping slot montage and must keep playing.
import json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'fixes'))
import build_472 as A
from build_472 import *
HERE = os.path.dirname(os.path.abspath(__file__))      # the star imports overwrite HERE
A.HERE = HERE
ROOT = '/Game/CastleDefender/Characters/Enemies/Zombie/Anim/Hit'
MONT, ANIMI = CLS('AnimMontage'), CLS('AnimInstance')
def actor_d(b, member, pins, x, y, tag): return b.call(ACT, member, pins, x, y, pure=True, const=True, tag=tag)
def seli(b, a, c, pick, x, y):
    return b.math('SelectInt', [(it('A', default=a), None), (it('B', default=c), None), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)

def gen(live):
    L = live_links(live); G = Graph(); b = bpkit.B(G, 'zc472'); rw = []
    # ---- significance
    pl = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], 0, 0, pure=True, tag='Player')
    dn = actor_d(b, 'GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 250, 0, 'Dist'); G.link(pl, 'ReturnValue', dn, 'OtherActor')
    dist = (dn, 'ReturnValue')
    near = b.dcmp('Less_DoubleDouble', dist, None, 500, 0, db='3000.0'); mid = b.dcmp('Less_DoubleDouble', dist, None, 500, 150, db='6000.0')
    n24 = seli(b, '2', '4', mid, 750, 150)
    N = b.math('SelectInt', [(it('A', default='1'), None), (it('B'), n24), (bo('bPickA', default='false'), near)], it('ReturnValue', out=True), 1000, 75)
    inc = b.i2('Add_IntInt', b.get('ThinkTick', INT, 0, 300), None, 250, 300, db='1')
    st1 = b.set('ThinkTick', INT, inc, 500, 300)
    rem = b.i2('Percent_IntInt', b.get('ThinkTick', INT, 500, 500), N, 1250, 300)
    run = b.branch(b.icmp('EqualEqual_IntInt', rem, None, 1500, 400, db='0'), 1750, 300, tag='IfThinkNow')
    G.link(st1, 'then', run, 'execute')
    seen = actor_d(b, 'WasRecentlyRendered', [fl('Tolerance', default='0.200000'), bo('ReturnValue', out=True)], 1750, 600, 'Seen')
    full = b.b2('BooleanOR', near, (seen, 'ReturnValue'), 2000, 600)
    cmc_i = b.self_(None, None, full, 2250, 600, da='0.0', db='0.1')
    act_i = b.self_(None, None, full, 2250, 750, da='0.0', db='0.25')
    cmcget = '%s.%s' % L[('K2Node_CallFunction_ZB79', 'self')][0]     # the live Get CharacterMovement
    t1 = b.call(CLS('ActorComponent'), 'SetComponentTickInterval', [fl('TickInterval', default='0.0')], 2500, 300, tag='CmcRate'); b.wire(cmc_i, t1, 'TickInterval')
    t2 = b.call(ACT, 'SetActorTickInterval', [fl('TickInterval', default='0.0')], 2800, 300, tag='ActRate'); b.wire(act_i, t2, 'TickInterval')
    G.link(run, 'then', t1, 'execute'); G.link(t1, 'then', t2, 'execute')
    rw += [R('K2Node_IfThenElse_ZB20.else', st1 + '.execute'), R(t2 + '.then', 'CX_501.execute'), {'from': cmcget, 'to': t1 + '.self'}]
    # ---- hit-stop: first thing on a live zombie
    frac = b.d2('Multiply_DoubleDouble', b.get('MaxHP', DBL, 0, 1000), None, 250, 1000, db='0.25')
    hv = b.math('GreaterEqual_DoubleDouble', [(D('A', default='0.0'), None), (D('B', default='0.0'), frac)], bo('ReturnValue', out=True), 500, 1000)
    ih = b.branch(hv, 750, 900, tag='IfHeavy')
    sd = b.setm('CustomTimeDilation', ACT, fl('v', default='0.020000'), None, None, 1000, 900)
    tm = b.timer('HitStopEnd', 1300, 900, dtime='0.06', loop=False); G.link(ih, 'then', sd, 'execute'); G.link(sd, 'then', tm, 'execute')
    nxt = L[('K2Node_IfThenElse_ZB62', 'else')][0][0]
    rw += [R('K2Node_IfThenElse_ZB62.else', ih + '.execute'), R(ih + '.else', nxt + '.execute'), R(tm + '.then', nxt + '.execute'),
           {'from': 'K2Node_Event_ZB60.Damage', 'to': hv[0] + '.A'}]
    b.event('HitStopEnd', [], 0, 1250)
    se = b.setm('CustomTimeDilation', ACT, fl('v', default='1.000000'), None, None, 300, 1250)
    G.link('HitStopEnd', 'then', se, 'execute')
    # ---- brute flinch
    causer = 'K2Node_Event_ZB60.DamageCauser'
    anim = '%s.%s' % L[('Ps_CX_195', 'self')][0]
    age = b.d2('Subtract_DoubleDouble', b.now(0, 1500), b.get('LastFlinchAt', DBL, 0, 1650), 250, 1500)
    due = b.dcmp('Greater_DoubleDouble', age, None, 500, 1500, db='1.0'); iv = b.valid(None, 500, 1650)
    ifd = b.branch(b.b2('BooleanAND', due, iv, 750, 1550), 1000, 1500, tag='IfFlinch')
    sf = b.set('LastFlinchAt', DBL, b.now(1000, 1700), 1250, 1500); G.link(ifd, 'then', sf, 'execute')
    cl = actor_d(b, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 0, 1850, 'CauserLoc'); me = actor_d(b, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 0, 2000, 'MyLoc')
    fw = actor_d(b, 'GetActorForwardVector', [V('ReturnValue', out=True)], 0, 2150, 'MyFwd')
    to = b.v2('Subtract_VectorVector', (cl, 'ReturnValue'), (me, 'ReturnValue'), 250, 1900)
    nrm = b.math('Normal', [(V('A'), to), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 500, 1900)
    dot = b.math('Dot_VectorVector', [(V('A'), (fw, 'ReturnValue')), (V('B'), nrm)], D('ReturnValue', out=True), 750, 2000)
    ifb = b.branch(b.dcmp('Less_DoubleDouble', dot, None, 1000, 2000, db='0.0'), 1500, 1500, tag='IfBehind'); G.link(sf, 'then', ifb, 'execute')
    def play(nm, y):
        return b.call(ANIMI, 'Montage_Play', [dict(ob('MontageToPlay', MONT), dobj='%s/%s.%s' % (ROOT, nm, nm)), fl('InPlayRate', default='3.000000'),
                      {'name': 'ReturnValueType', 'cat': 'byte', 'obj': ENUM('EMontagePlayReturnType'), 'default': 'MontageLength'},
                      fl('InTimeToStartMontageAt', default='0.000000'), bo('bStopAllMontages', default='false'), fl('ReturnValue', out=True, default='0.0')], 1800, y, tag='Flinch')
    pb, pf = play('AM_ZFlinch_Back', 1500), play('AM_ZFlinch_Front', 1700)
    G.link(ifb, 'then', pb, 'execute'); G.link(ifb, 'else', pf, 'execute')
    rw += [R('CX_531.then', ifd + '.execute'), {'from': causer, 'to': iv[0] + '.Object'}, {'from': causer, 'to': cl + '.self'},
           {'from': anim, 'to': pb + '.self'}, {'from': anim, 'to': pf + '.self'}]
    open(os.path.join(HERE, 'zombie_c_paste.txt'), 'w', newline='\r\n').write(G.render()); print('zombie_c_paste.txt', len(G.nodes), 'nodes')
    json.dump({'blueprint': 'BP_Zombie', 'note': '#472 fix C: significance, hit-stop, brute flinch', 'pastes': ['zombie_c_paste.txt'], 'rewires': rw},
              open(os.path.join(HERE, 'zombie_c_manifest.json'), 'w'), indent=1)

if __name__ == '__main__':
    z = A.to_graph(sys.argv[1])
    gen(open(z, encoding='utf-8', errors='replace', newline='').read().replace('\r\n', '\n'))
    A.build(z, 'zombie_c_manifest.json', [], 'zombie_c_merged.txt')
    print('OK: paste zombie_c_merged.txt into BP_Zombie')
