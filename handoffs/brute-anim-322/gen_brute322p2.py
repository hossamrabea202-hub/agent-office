# #322 part 2: Flesh Brute animation polish (adjustedfilm, 2026-10-31; owner W: "polish big mouth animations").
#   "<blender python>" -I gen_brute322p2.py  ->  ABP_FleshBrute_EventGraph.txt, ABP_FleshBrute_AnimGraph.txt,
#                                               BP_FleshBrute_EventGraph_v2.txt (whole graph, replaces the live one),
#                                               ABP_VARIABLES_BPVar.txt, BRUTE_VARIABLES_BPVar.txt
# Built on handoffs/exports/adjustedfilm/brute-322/BP_FleshBrute_EventGraph.txt (Master, 2026-10-31 15:18).
#
# Why: the brute plays every clip with SkeletalMeshComponent.PlayAnimation (single-node mode), which cuts hard from clip
# to clip. Now the mesh runs ABP_FleshBrute: two clip channels (A / B) shown through a Two Way Blend. Every new clip goes
# into the idle channel and the blend crossfades to it over BlendTime (0.25 s, eased), so nothing snaps.
#   FB_Play(Anim, Loop)  = the old PlayAnimation (rate back to 1; one-shots start at 0, loops at a random point)
#   FB_Rate(Rate)        = the old SetPlayRate     (on the live channel; -1 still plays backwards)
#   FB_Pos(Pos)          = the old SetPosition     (on the live channel)
# Non-looping clips hold their last frame (as before: death, laying, bursts). Looping clips (walk / run / crawl) are the
# gait: their speed follows the real move speed (speed / max speed, clamped 0.8..1.2) x Heavy (0.92), so heavy steps
# match the ground better (kept within the +-20 % rule of INDUSTRY_SECRETS 3.4). Every brute rolls its own Jitter (0.9..1.06) at
# spawn, so a group never walks in lock-step. GlobalAnimRateScale (used 25x by the graph) still scales everything.
# HP x4: the three MaxHP sets (260 / 60 / 100 by ZType) become 1040 / 240 / 400.
import os, re, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

LIVE = os.path.join(HERE, '..', 'exports', 'adjustedfilm', 'brute-322', 'BP_FleshBrute_EventGraph.txt')
P_ABP = '/Game/CastleDefender/Characters/Enemies/FleshBrute/ABP_FleshBrute'
ABPC = '"/Script/Engine.AnimBlueprintGeneratedClass\'%s.ABP_FleshBrute_C\'"' % P_ABP
ANIMI, SEQB, PMOVE, MOVEC = CLS('AnimInstance'), CLS('AnimSequenceBase'), CLS('PawnMovementComponent'), CLS('MovementComponent')
IDLE = '/Game/CastleDefender/Characters/Enemies/FleshBrute/Anims/FB_ZA_Idle_A.FB_ZA_Idle_A'
F = lambda n, d=None, out=False: fl(n, out=out, default=d)          # float params of engine functions
SEQV = ob('v', SEQB)


class B(bpkit.B):
    def ev(s, nm, member, outs, x, y):
        """AnimInstance override event (BlueprintUpdateAnimation / BlueprintInitializeAnimation)."""
        s.G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ANIMI, member), 'bOverrideFunction=True'],
                 [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (ANIMI, member)}, ex('then', True)] + outs, x, y)
        return nm


# ===================================================================================================== ABP EventGraph
G = Graph(); b = B(G, 'fb'); g = b.get
# ---- BlueprintInitializeAnimation: own rhythm per brute
b.ev('fbInit', 'BlueprintInitializeAnimation', [], 0, -1200)
b.chain('fbInit', b.set('Jitter', DBL, b.rnd(None, None, 0, -1000) if False else b.math('RandomFloatInRange', [(D('Min', default='0.9'), g('JitterMin', DBL, -200, -950)), (D('Max', default='1.06'), g('JitterMax', DBL, -200, -900))], D('ReturnValue', out=True), 0, -1000), 300, -1200))

# ---- FB_Play(Anim, Loop): load the idle channel, flip to it
ANIMP, LOOPP = ob('Anim', SEQB), bo('Loop', default='false')
b.event('FB_Play', [dict(ANIMP), dict(LOOPP)], 0, -600)
br = b.branch(g('UseB', BOOL, 0, -400), 300, -600, tag='IfB')
G.link('FB_Play', 'then', br, 'execute')
for k, (pin, cur, nxt, flip) in enumerate((('then', 'B', 'A', 'false'), ('else', 'A', 'B', 'true'))):
    y = -700 + 300 * k
    n1 = b.set('Seq' + nxt, SEQV, ('FB_Play', 'Anim'), 600, y)
    # loops start at a random point of the cycle (INDUSTRY_SECRETS 3.4 #9), one-shots at 0 like PlayAnimation
    pl = b.call(SEQB, 'GetPlayLength', [F('ReturnValue', out=True)], 600, y + 150, target=('FB_Play', 'Anim'), pure=True, const=True)
    rs = b.math('RandomFloatInRange', [(D('Min', default='0.0'), None), (D('Max'), (pl, 'ReturnValue'))], D('ReturnValue', out=True), 750, y + 150)
    n2 = b.set('Time' + nxt, DBL, b.self_(rs, None, ('FB_Play', 'Loop'), 850, y + 150), 850, y)
    n3 = b.set('Loop' + nxt, BOOL, ('FB_Play', 'Loop'), 1100, y)
    n4 = b.set('Rate' + nxt, dict(DBL, default='1.0'), None, 1350, y)
    n5 = b.set('UseB', dict(BOOL, default=flip), None, 1600, y)
    G.link(br, pin, n1, 'execute'); b.chain(n1, n2, n3, n4, n5)

# ---- FB_Rate(Rate) / FB_Pos(Pos): on the live channel
for k, (evn, par, var) in enumerate((('FB_Rate', 'Rate', 'Rate'), ('FB_Pos', 'Pos', 'Time'))):
    y = 0 + 400 * k
    b.event(evn, [D(par)], 0, y)
    br = b.branch(g('UseB', BOOL, 0, y + 200), 300, y, tag='If' + par)
    G.link(evn, 'then', br, 'execute')
    G.link(br, 'then', b.set(var + 'B', DBL, (evn, par), 600, y - 100), 'execute')
    G.link(br, 'else', b.set(var + 'A', DBL, (evn, par), 600, y + 100), 'execute')

# ---- BlueprintUpdateAnimation(DeltaTimeX)
Y = 1200
b.ev('fbUpdate', 'BlueprintUpdateAnimation', [F('DeltaTimeX', out=True)], 0, Y)
dt = ('fbUpdate', 'DeltaTimeX')
# blend: Alpha moves to 0 (A) or 1 (B) in BlendTime (linear crossfade)
tgt = b.self_(None, None, g('UseB', BOOL, 200, Y + 450), 400, Y + 400, da='1.0', db='0.0')
spd = b.d2('Divide_DoubleDouble', None, b.math('FMax', [(D('A', default='0.05'), g('BlendTime', DBL, 200, Y + 600)), (D('B', default='0.05'), None)], D('ReturnValue', out=True), 400, Y + 600), 600, Y + 550, da='1.0')
ai = b.math('FInterpTo_Constant', [(D('Current'), g('Alpha', DBL, 600, Y + 300)), (D('Target'), tgt), (D('DeltaTime'), dt), (D('InterpSpeed'), spd)], D('ReturnValue', out=True), 850, Y + 350)
sa = b.set('Alpha', DBL, ai, 1100, Y)
G.link('fbUpdate', 'then', sa, 'execute')
# gait: real speed / max speed of the brute, clamped, x Heavy
pawn = b.call(ANIMI, 'TryGetPawnOwner', [ob('ReturnValue', PAWN, out=True)], 1100, Y + 900, pure=True, const=True)
G.nodes[-1][3][0]['hidden'] = True                         # self (the anim instance) hidden
bv = b.branch(b.valid((pawn, 'ReturnValue'), 1350, Y + 250), 1350, Y, tag='IfPawn')
G.link(sa, 'then', bv, 'execute')
vel = b.call(ACT, 'GetVelocity', [V('ReturnValue', out=True)], 1350, Y + 900, target=(pawn, 'ReturnValue'), pure=True, const=True)
vs = b.math('VSize', [(V('A'), (vel, 'ReturnValue'))], D('ReturnValue', out=True), 1600, Y + 900)
mc = b.call(PAWN, 'GetMovementComponent', [ob('ReturnValue', PMOVE, out=True)], 1350, Y + 1100, target=(pawn, 'ReturnValue'), pure=True, const=True)
mx = b.call(MOVEC, 'GetMaxSpeed', [F('ReturnValue', out=True)], 1600, Y + 1100, target=(mc, 'ReturnValue'), pure=True, const=True)
mx1 = b.math('FMax', [(D('A', default='1.0'), (mx, 'ReturnValue')), (D('B', default='1.0'), None)], D('ReturnValue', out=True), 1850, Y + 1100)
ratio = b.d2('Divide_DoubleDouble', vs, mx1, 2050, Y + 950)
gc = b.math('FClamp', [(D('Value'), ratio), (D('Min', default='0.8'), g('GaitMin', DBL, 2050, Y + 1150)), (D('Max', default='1.2'), g('GaitMax', DBL, 2050, Y + 1250))], D('ReturnValue', out=True), 2300, Y + 1000)
gh = b.d2('Multiply_DoubleDouble', gc, g('Heavy', DBL, 2300, Y + 1200), 2550, Y + 1000)
sg = b.set('Gait', DBL, gh, 2800, Y - 200)
G.link(bv, 'then', sg, 'execute')
# advance both channels: T += dt * Rate * (Loop ? clamp(Gait * Jitter, 0.8, 1.2) : Jitter); loop -> wrap, else hold (clamp) at the ends
prev = None
for k, c in enumerate('AB'):
    y = Y + 1600 + 900 * k
    # loops: Gait x Jitter kept inside 0.8..1.2 (INDUSTRY_SECRETS 3.4 #2, the +-20 % rule); one-shots: Jitter only
    gj = b.clamp(b.d2('Multiply_DoubleDouble', g('Gait', DBL, 3100, y + 250), g('Jitter', DBL, 3100, y + 300), 3300, y + 250), '0.8', '1.2', 3500, y + 250)
    gl = b.self_(gj, g('Jitter', DBL, 3500, y + 400), g('Loop' + c, BOOL, 3500, y + 450), 3700, y + 250)
    step = b.d2('Multiply_DoubleDouble', dt, g('Rate' + c, DBL, 2900, y + 100), 3100, y)
    t1 = b.d2('Add_DoubleDouble', g('Time' + c, DBL, 3700, y - 150), b.d2('Multiply_DoubleDouble', step, gl, 3700, y + 50), 3900, y)
    ln = b.call(SEQB, 'GetPlayLength', [F('ReturnValue', out=True)], 3900, y + 250, target=g('Seq' + c, SEQV, 3700, y + 250), pure=True, const=True)
    wr = b.math('FWrap', [(D('Value'), t1), (D('Min', default='0.0'), None), (D('Max'), (ln, 'ReturnValue'))], D('ReturnValue', out=True), 4150, y - 50)
    cl = b.math('FClamp', [(D('Value'), t1), (D('Min', default='0.0'), None), (D('Max'), (ln, 'ReturnValue'))], D('ReturnValue', out=True), 4150, y + 150)
    pick = b.self_(wr, cl, g('Loop' + c, BOOL, 4150, y + 350), 4400, y)
    st_ = b.set('Time' + c, DBL, pick, 4650, y - 300)
    vs_ = b.branch(b.valid(g('Seq' + c, SEQV, 4400, y - 150), 4400, y - 100), 4400, y - 300, tag='IfSeq' + c)   # no clip -> skip
    if prev is None:
        G.link(bv, 'else', vs_, 'execute'); G.link(sg, 'then', vs_, 'execute')
    else:
        G.link(prev[0], 'then', vs_, 'execute'); G.link(prev[1], 'else', vs_, 'execute')
    G.link(vs_, 'then', st_, 'execute')
    prev = (st_, vs_)


def check_write(G, fname):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    names = [n[0] for n in G.nodes]
    if bad or len(names) != len(set(names)): raise SystemExit('bad links %s / dup %s' % (bad[:10], [n for n in names if names.count(n) > 1][:5]))
    open(os.path.join(HERE, fname), 'w', newline='\r\n').write(G.render())
    print('%s: nodes %d, links %d' % (fname, len(G.nodes), len(G.links)))


check_write(G, 'ABP_FleshBrute_EventGraph.txt')

# ===================================================================================================== ABP AnimGraph
# EvalA / EvalB (Sequence Evaluator, Sequence + Explicit Time as pins) -> Two Way Blend (A, B, Alpha) -> (Master: 1 wire to
# Output Pose).
TAILP = 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
gid = lambda tag: uuid.uuid5(uuid.NAMESPACE_URL, 'brute322p2/' + tag).hex.upper()
POSE = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.PoseLink\'"'


def pin(node, name, cat, obj='None', sub='', out=False, link=None, default=None, friendly=None):
    s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (gid(node + '.' + name), name)
    if friendly: s += 'PinFriendlyName=%s,' % friendly
    if out: s += 'Direction="EGPD_Output",'
    s += ('PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),'
          'PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,'
          'PinType.bSerializeAsSinglePrecisionFloat=False,') % (cat, sub, obj)
    if default is not None: s += 'DefaultValue="%s",' % default
    if link: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % (n_, gid(n_ + '.' + p_)) for n_, p_ in link)
    return '   ' + s + TAILP


def block(cls, name, x, y, props, pins):
    return '\n'.join(['Begin Object Class=%s Name="%s"' % (cls, name)] + ['   ' + p for p in props] +
                     ['   NodePosX=%d' % x, '   NodePosY=%d' % y, '   NodeGuid=%s' % gid(name)] + pins + ['End Object'])


def vget(name, var, cat, obj, sub, x, y, to):
    return block('/Script/BlueprintGraph.K2Node_VariableGet', name, x, y, ['VariableReference=(MemberName="%s",bSelfContext=True)' % var],
                 [pin(name, var, cat, obj, sub, out=True, link=[to]),
                  pin(name, 'self', 'object', ABPC, friendly='NSLOCTEXT("K2Node", "Target", "Target")').replace('bHidden=False', 'bHidden=True')])


SEQOBJ = SEQB
AG = []
for c, y in (('A', 0), ('B', 400)):
    ev = 'FB_Eval' + c
    AG.append(block('/Script/AnimGraph.AnimGraphNode_SequenceEvaluator', ev, 400, y,
                    ['Node=(Sequence="/Script/Engine.AnimSequence\'%s\'",bTeleportToExplicitTime=True)' % IDLE,
                     'ShowPinForProperties(0)=(PropertyName="Sequence",PropertyFriendlyName="Sequence",CategoryName="Settings",bShowPin=True,bCanToggleVisibility=True)',
                     'ShowPinForProperties(1)=(PropertyName="ExplicitTime",PropertyFriendlyName="Explicit Time",CategoryName="Settings",bShowPin=True,bCanToggleVisibility=True)'],
                    [pin(ev, 'Pose', 'struct', POSE, out=True, link=[('FB_Blend', c)]),
                     pin(ev, 'Sequence', 'object', SEQOBJ, link=[('FB_GetSeq' + c, 'Seq' + c)]),
                     pin(ev, 'ExplicitTime', 'real', sub='float', default='0.0', link=[('FB_GetTime' + c, 'Time' + c)])]))
    AG.append(vget('FB_GetSeq' + c, 'Seq' + c, 'object', SEQOBJ, '', 100, y, (ev, 'Sequence')))
    AG.append(vget('FB_GetTime' + c, 'Time' + c, 'real', 'None', 'double', 100, y + 120, (ev, 'ExplicitTime')))
AG.append(block('/Script/AnimGraph.AnimGraphNode_TwoWayBlend', 'FB_Blend', 800, 200,
                ['Node=(AlphaScaleBiasClamp=(bMapRange=False,bClampResult=True,ClampMin=0.0,ClampMax=1.0,bInterpResult=False))',
                 'ShowPinForProperties(0)=(PropertyName="Alpha",PropertyFriendlyName="Alpha",CategoryName="Settings",bShowPin=True,bCanToggleVisibility=True)'],
                [pin('FB_Blend', 'A', 'struct', POSE, link=[('FB_EvalA', 'Pose')]),
                 pin('FB_Blend', 'B', 'struct', POSE, link=[('FB_EvalB', 'Pose')]),
                 pin('FB_Blend', 'Alpha', 'real', sub='float', default='0.0', link=[('FB_GetAlpha', 'Alpha')]),
                 pin('FB_Blend', 'Pose', 'struct', POSE, out=True)]))
AG.append(vget('FB_GetAlpha', 'Alpha', 'real', 'None', 'double', 500, 800, ('FB_Blend', 'Alpha')))
open(os.path.join(HERE, 'ABP_FleshBrute_AnimGraph.txt'), 'w', newline='\r\n').write('\n'.join(AG) + '\n')
print('ABP_FleshBrute_AnimGraph.txt: %d nodes' % len(AG))

# ===================================================================================================== BPVar lines
DT = 'PinCategory="real",PinSubCategory="double"'
SEQT = 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.AnimSequenceBase\'"'
ABPVARS = [('SeqA', SEQT, IDLE, 'clip in channel A'), ('SeqB', SEQT, IDLE, 'clip in channel B'),
           ('TimeA', DT, '0.0', 'state'), ('TimeB', DT, '0.0', 'state'), ('RateA', DT, '1.0', 'state'), ('RateB', DT, '1.0', 'state'),
           ('LoopA', 'PinCategory="bool"', 'true', 'state'), ('LoopB', 'PinCategory="bool"', 'true', 'state'),
           ('UseB', 'PinCategory="bool"', 'false', 'state: B is the live channel'), ('Alpha', DT, '0.0', 'state: 0 = A, 1 = B'),
           ('Gait', DT, '1.0', 'state: speed match of the looping (gait) clips'), ('Jitter', DT, '1.0', 'rolled per brute at spawn'),
           ('JitterMin', DT, '0.9', 'slowest own rhythm'), ('JitterMax', DT, '1.06', 'fastest own rhythm'),
           ('Heavy', DT, '0.92', 'gait weight: below 1 = heavier, slower steps'), ('GaitMin', DT, '0.8', 'gait rate when nearly stopped (+-20 % rule)'),
           ('GaitMax', DT, '1.2', 'gait rate cap when pushed faster than max speed'), ('BlendTime', DT, '0.25', 's crossfade between clips')]
BRVARS = [('FBAnim', 'PinCategory="object",PinSubCategoryObject="%s"' % ABPC.strip('"'), '', 'the mesh\'s ABP_FleshBrute (set at BeginPlay)')]


def bpvars(rows, tag, fname, title):
    bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
        n, uuid.uuid5(uuid.NAMESPACE_URL, tag + n).hex.upper(), t, n, d)
    open(os.path.join(HERE, fname), 'w', newline='\r\n').write('# ' + title + '\n' + '\n'.join(bpv(*v[:3]) for v in rows) + '\n')
    print('%s: %d' % (fname, len(rows)))


bpvars(ABPVARS, 'brute322p2/abp/', 'ABP_VARIABLES_BPVar.txt', '#322 p2 ABP_FleshBrute - paste one line at a time on the VARIABLES header of My Blueprint, then Compile')
bpvars(BRVARS, 'brute322p2/bp/', 'BRUTE_VARIABLES_BPVar.txt', '#322 p2 BP_FleshBrute - paste on the VARIABLES header (after ABP_FleshBrute compiled), then Compile')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #322 part 2 variables\n\n## ABP_FleshBrute\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _t, d, m in ABPVARS: f.write('| %s | %s | %s |\n' % (n, d.split('.')[-1] or '-', m))
    f.write('\n## BP_FleshBrute\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _t, d, m in BRVARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))

# ===================================================================================================== BP_FleshBrute rewrite
txt = open(LIVE, encoding='utf-8').read().replace('\r\n', '\n')
blocks = re.findall(r'Begin Object Class=\S+ Name="[^"]+".*?\nEnd Object\n?', txt, re.S)
assert ''.join(blocks).strip() == txt.strip(), 'export has text outside node blocks'
byname = {re.search(r'Name="([^"]+)"', bl).group(1): bl for bl in blocks}
order = list(byname)
PINRE = re.compile(r'   CustomProperties Pin \((.*)\)\n')


def pins_of(bl):
    out = {}
    for p in PINRE.findall(bl):
        nm = re.search(r'PinName="([^"]*)"', p).group(1)
        lk = re.search(r'LinkedTo=\(([^)]*)\)', p)
        dv = re.search(r'(?:DefaultValue|DefaultObject)="([^"]*)"', p)
        out[nm] = {'id': re.search(r'PinId=(\w+)', p).group(1), 'links': [tuple(x.split()) for x in lk.group(1).split(',') if x] if lk else [],
                   'default': dv.group(1) if dv else None, 'raw': p}
    return out


def unlink(name, pinid, other, other_pinid):
    """remove 'other other_pinid,' from pin pinid of node name."""
    bl = byname[name]
    new = bl.replace('%s %s,' % (other, other_pinid), '', 1)
    assert new != bl, 'link %s.%s -> %s.%s not found' % (name, pinid, other, other_pinid)
    byname[name] = re.sub(r'LinkedTo=\(\),', '', new)


SKM = "MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.SkeletalMeshComponent'\""
REPL = {'PlayAnimation': ('FB_Play', [('NewAnimToPlay', 'Anim', 'object'), ('bLooping', 'Loop', 'bool')]),
        'SetPlayRate': ('FB_Rate', [('Rate', 'Rate', 'real')]),
        'SetPosition': ('FB_Pos', [('InPos', 'Pos', 'real')])}
added, nrep, gone = [], {}, []
for name in list(order):
    if name not in byname: continue          # a Mesh getter removed above
    bl = byname[name]
    m = re.search(r'FunctionReference=\(%s,MemberName="(\w+)"\)' % re.escape(SKM), bl)
    if not m or m.group(1) not in REPL: continue
    member, (newm, params) = m.group(1), REPL[m.group(1)]
    ps = pins_of(bl)
    for p in ps:
        if p not in ('execute', 'then', 'self') and ps[p]['links']: raise SystemExit('%s.%s is wired, not a default' % (name, p))
    x, y = (int(re.search(r'NodePos%s=(-?\d+)' % a, bl).group(1)) for a in 'XY')
    # the old target (a Mesh getter) loses this link; getters left with no links are removed
    for (on, opid) in ps['self']['links']:
        unlink(on, None, name, ps['self']['id'])
        if 'LinkedTo=(' not in byname[on]: gone.append(on); del byname[on]; order.remove(on)
    lk = lambda pn: 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in ps[pn]['links']) if ps[pn]['links'] else ''
    getn, selfid = 'FBGet_' + name, gid(name + '.fbself')
    lines = ['Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="%s"' % name,
             '   FunctionReference=(MemberParent=%s,MemberName="%s")' % (ABPC, newm),
             '   NodePosX=%d' % x, '   NodePosY=%d' % y, '   NodeGuid=%s' % gid(name + '.guid'),
             '   ' + 'CustomProperties Pin (' + ps['execute']['raw'] + ')',
             '   ' + 'CustomProperties Pin (' + ps['then']['raw'] + ')',
             '   CustomProperties Pin (PinId=%s,PinName="self",PinFriendlyName=NSLOCTEXT("K2Node", "Target", "Target"),PinType.PinCategory="object",PinType.PinSubCategory="",'
             'PinType.PinSubCategoryObject=%s,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,'
             'PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,LinkedTo=(%s %s,),%s'
             % (selfid, ABPC, getn, gid(getn + '.out'), TAILP)]
    for old, new, cat in params:
        dv = ps[old]['default']
        if cat == 'object':
            lines.append('   CustomProperties Pin (PinId=%s,PinName="%s",PinType.PinCategory="object",PinType.PinSubCategory="",PinType.PinSubCategoryObject=%s,'
                         'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,'
                         'PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultObject="%s",%s'
                         % (gid(name + '.' + new), new, SEQB, dv, TAILP))
        else:
            sub = 'double' if cat == 'real' else ''
            lines.append('   CustomProperties Pin (PinId=%s,PinName="%s",PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=None,'
                         'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,'
                         'PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultValue="%s",%s'
                         % (gid(name + '.' + new), new, cat, sub, dv, TAILP))
    lines.append('End Object\n')
    byname[name] = '\n'.join(lines)
    added.append(block('/Script/BlueprintGraph.K2Node_VariableGet', getn, x - 40, y + 140, ['VariableReference=(MemberName="FBAnim",bSelfContext=True)'],
                       ['   CustomProperties Pin (PinId=%s,PinName="FBAnim",Direction="EGPD_Output",PinType.PinCategory="object",PinType.PinSubCategory="",'
                        'PinType.PinSubCategoryObject=%s,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,'
                        'PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,LinkedTo=(%s %s,),%s'
                        % (gid(getn + '.out'), ABPC, name, selfid, TAILP),
                        '   CustomProperties Pin (PinId=' + gid(getn + '.self') + ',PinName="self",PinFriendlyName=NSLOCTEXT("K2Node", "Target", "Target"),PinType.PinCategory="object",PinType.PinSubCategory="",'
                        'PinType.PinSubCategoryObject="/Script/Engine.BlueprintGeneratedClass\'/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute.BP_FleshBrute_C\'",'
                        'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,'
                        'PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,' + TAILP.replace('bHidden=False', 'bHidden=True')]) + '\n')
    nrep[member] = nrep.get(member, 0) + 1

# ---- BeginPlay: Mesh -> GetAnimInstance -> Cast to ABP_FleshBrute -> FBAnim, before everything else
ev, first = 'K2Node_Event_ZB0', 'QX_CallFunction_1'
pe, pf = pins_of(byname[ev]), pins_of(byname[first])
assert [l[0] for l in pe['then']['links']] == [first]
unlink(ev, None, first, pf['execute']['id']); unlink(first, None, ev, pe['then']['id'])
G2 = Graph(); b2 = B(G2, 'fbbp')
x0, y0 = (int(re.search(r'NodePos%s=(-?\d+)' % a, byname[ev]).group(1)) for a in 'XY')
mesh = b2.get('Mesh', ob('v', SKEL), x0, y0 - 500)
gai = b2.call(SKEL, 'GetAnimInstance', [ob('ReturnValue', ANIMI, out=True)], x0 + 220, y0 - 500, target=mesh, pure=True, const=True)
cst = 'FBCastABP'; cast(G2, cst, ABPC, 'AsABP_FleshBrute', x0 + 500, y0 - 400); b2.wire((gai, 'ReturnValue'), cst, 'Object')
sfb = b2.set('FBAnim', ob('v', ABPC), (cst, 'AsABP_FleshBrute'), x0 + 800, y0 - 400)
G2.link(cst, 'then', sfb, 'execute')
r2 = G2.render()
# exec in/out of the insert: (event.then -> cast.execute), (set.then / cast.CastFailed -> first.execute)
ids = dict(re.findall(r'Name="(\w+)"[^\n]*\n(?:(?!End Object).*\n)*?', r2) and [])
def pid(node, pn):
    bl = re.search(r'Name="%s".*?End Object' % node, r2, re.S).group(0)
    return re.search(r'PinId=(\w+),PinName="%s"' % pn, bl).group(1)
def addlink(node_txt, pn, other, opid):
    return re.sub(r'(PinId=\w+,PinName="%s",(?:(?!\n).)*?)(PersistentGuid=)' % pn,
                  lambda m: (m.group(1).replace('LinkedTo=(', 'LinkedTo=(%s %s,' % (other, opid), 1) if 'LinkedTo=(' in m.group(1)
                             else m.group(1) + 'LinkedTo=(%s %s,),' % (other, opid)) + m.group(2), node_txt, count=1)
byname[ev] = addlink(byname[ev], 'then', cst, pid(cst, 'execute'))
r2 = addlink(r2, 'execute', ev, pe['then']['id'])          # first match in r2 = the cast's execute? make sure
assert re.search(r'Name="%s".*?PinName="execute"[^\n]*%s' % (cst, ev), r2, re.S), 'cast exec link'
byname[first] = addlink(byname[first], 'execute', sfb, pid(sfb, 'then'))
byname[first] = addlink(byname[first], 'execute', cst, pid(cst, 'CastFailed'))
r2 = re.sub(r'(Name="%s".*?PinName="then",(?:(?!\n).)*?)(PersistentGuid=)' % sfb, lambda m: m.group(1) + 'LinkedTo=(%s %s,),' % (first, pf['execute']['id']) + m.group(2), r2, count=1, flags=re.S)
r2 = re.sub(r'(Name="%s".*?PinName="CastFailed",(?:(?!\n).)*?)(PersistentGuid=)' % cst, lambda m: m.group(1) + 'LinkedTo=(%s %s,),' % (first, pf['execute']['id']) + m.group(2), r2, count=1, flags=re.S)

# ---- HP x4: the three MaxHP sets
hp = 0
for name in order:
    bl = byname[name]
    if 'K2Node_VariableSet' in bl.split('\n')[0] and 'VariableReference=(MemberName="MaxHP"' in bl:
        new = re.sub(r'(PinName="MaxHP",[^\n]*?DefaultValue=")([\d.]+)"', lambda m: '%s%.1f"' % (m.group(1), float(m.group(2)) * 4), bl, count=1)
        assert new != bl; byname[name] = new; hp += 1
assert hp == 3, hp

out = ''.join(byname[n] if byname[n].endswith('\n') else byname[n] + '\n' for n in order) + ''.join(added) + r2
open(os.path.join(HERE, 'BP_FleshBrute_EventGraph_v2.txt'), 'w', newline='\r\n').write(out)
print('BP_FleshBrute_EventGraph_v2.txt: replaced %s, +%d FBAnim getters, -%d unused Mesh getters, BeginPlay +4, MaxHP x4 on %d sets' % (nrep, len(added), len(gone), hp))
