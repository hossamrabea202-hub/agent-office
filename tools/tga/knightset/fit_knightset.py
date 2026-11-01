# Yellow Eagle set (#367, TGA): fit the canonical-frame pieces onto the knight's reference pose (#368 dump) and export
# them in KNIGHT SPACE, the frame the Obsidian v2 set system expects (setup_set_v2_ue.py: offset = inverse(bone-in-knight)).
#   blender -b <piece>_tex.blend -P fit_knightset.py      (env WORK, PIECE, REPO) -> WORK/out/fbx_knight/*.fbx + fit_<piece>.json
# Knight space in Blender = UE mesh component space with Y flipped (UE FBX import maps Blender (x, y, z) m to UE (x, -y, z) cm):
# metres, Z up, the knight faces -Y, its left side is +X. Only bone positions are used (no licensed mesh data).
# Each piece is placed from anatomical landmarks, not bone axes (the bone rolls are arbitrary):
#   Gauntlets: wrist at hand_l, fingers along hand_l -> middle fingertip, thumb side toward index_01 (orthogonalised).
#   Greaves:   up along ankle -> knee (foot_l -> calf_l), shin toward the foot's forward direction, bottom 3 cm under the ankle.
#   Sabatons:  sole origin on the ground under foot_l, toe along foot_l -> ball_l (horizontal), up +Z.
# R = the L fit computed on the mirrored right-side landmarks, then mirrored back (R meshes are S_x L in the tex blends).
import bpy, os, json, math, numpy as np
PIECE = os.environ.get('PIECE', 'Gauntlets'); NAME = 'SM_Eagle' + PIECE
REPO = os.environ.get('REPO', r'R:\\'); D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath)
OUT = os.path.join(D, 'out', 'fbx_knight'); os.makedirs(OUT, exist_ok=True)
# per-piece uniform scale over the measured fit: room for the knight's own armour under the plates (tune after the UE look)
EASE = {'Gauntlets': 1.06, 'Greaves': 1.08, 'Sabatons': 1.05}[PIECE]
ZEASE = 1.15                                                       # sabatons only

def load_refpose(p):
    bones = {}
    for ln in open(p, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip(): continue
        f = ln.rstrip('\n').split('\t')
        wl = [float(x) for x in f[4].split(',')]
        bones[f[0]] = np.array([wl[0], -wl[1], wl[2]]) / 100.0       # UE cm -> Blender knight space m
    return bones
B = load_refpose(os.path.join(REPO, 'handoffs', 'exports', 'master', 'knight_refpose.txt'))
SX = np.diag([-1.0, 1.0, 1.0])
def nz(v): return v / np.linalg.norm(v)
def side_pts(s):
    if s == 'l': return {k[:-2]: v for k, v in B.items() if k.endswith('_l')}
    return {k[:-2]: SX @ v for k, v in B.items() if k.endswith('_r')}   # mirrored onto the left

def mesh_pts():
    o = bpy.data.objects[NAME + '_L']; return np.array([v.co[:] for v in o.data.vertices])

def frame_L(P, V):
    """returns (R 3x3 columns = canonical X, Y, Z in knight space, origin, scale, info) for the left side"""
    info = {}
    if PIECE == 'Gauntlets':
        tip = P['middle_03'] + (P['middle_03'] - P['middle_02']) * 0.9
        f = nz(tip - P['hand']); ac = P['index_01'] - P['pinky_01']; X = nz(ac - f * f.dot(ac)); Z = -f; Y = np.cross(Z, X)
        L_k = np.linalg.norm(tip - P['hand']); L_m = -V[:, 2].min()
        s = EASE * L_k / L_m; org = P['hand']
        # centre the plate fingers on the knight's finger bones: knight _02 joints in the canonical frame vs the mesh finger band
        kn = np.array([R_.T @ (P['%s_02' % n] - org) / s for n in ('index', 'middle', 'ring', 'pinky') for R_ in [np.column_stack([X, Y, Z])]])
        band = V[(V[:, 2] < -L_m * 0.55) & (V[:, 2] > -L_m * 0.8)]
        d = kn.mean(0) - (band.min(0) + band.max(0)) / 2; d[2] = 0; org = org + np.column_stack([X, Y, Z]) @ d * s
        info.update(finger_centre_shift_cm=(d * s * 100).round(2).tolist())
        info.update(knight_wrist_to_tip_cm=L_k * 100, mesh_wrist_to_tip_cm=L_m * 100,
                    thumb_palmward_cm=float((P['thumb_01'] - P['hand']).dot(Y) * 100), thumb_side_cm=float((P['thumb_01'] - P['hand']).dot(X) * 100))
    elif PIECE == 'Greaves':
        Z = nz(P['calf'] - P['foot']); fwd = P['ball'] - P['foot']; fwd[2] = 0; fwd = nz(nz(fwd) + np.array([0, -1.0, 0]))
        front = nz(fwd - Z * Z.dot(fwd)); Y = -front; X = np.cross(Y, Z)
        L_k = np.linalg.norm(P['calf'] - P['foot']); L_m = V[:, 2].max()
        s = EASE; org = P['foot'] - Z * 0.03
        info.update(knee_to_ankle_cm=L_k * 100, greave_height_cm=L_m * 100 * s, top_below_knee_cm=float((P['calf'] - (org + Z * L_m * s)).dot(Z) * 100))
    else:
        t = P['ball'] - P['foot']; t[2] = 0; toe = nz(t); Y = -toe; Z = np.array([0, 0, 1.0]); X = np.cross(Y, Z)
        s = EASE; org = np.array([P['foot'][0], P['foot'][1], 0.0])
        R = np.column_stack([X, Y, Z * ZEASE])                       # taller instep over the knight's foot (ball bone 1.9 cm, ankle 7.8 cm up)
        info.update(z_ease=ZEASE)
        info['det'] = 1.0; info['scale'] = float(s); info['origin_cm'] = (org * 100).round(2).tolist()
        return R, org, s, info
        info.update(toe_out_deg=float(math.degrees(math.atan2(toe[0], -toe[1]))), ankle_height_cm=float(P['foot'][2] * 100),
                    sole_len_cm=float((V[:, 1].max() - V[:, 1].min()) * 100 * s))
    R = np.column_stack([X, Y, Z]); info['det'] = float(np.linalg.det(R)); info['scale'] = float(s); info['origin_cm'] = (org * 100).round(2).tolist()
    return R, org, s, info

V = mesh_pts(); rep = {'piece': PIECE, 'ease': EASE}
M = {}
for s in 'lr':
    R, org, sc, info = frame_L(side_pts(s), V)
    A = np.eye(4); A[:3, :3] = R * sc; A[:3, 3] = org
    if s == 'r':
        S4 = np.eye(4); S4[0, 0] = -1; A = S4 @ A @ S4                 # back to the right side; applied to S_x L meshes = proper rigid + scale
        info['origin_cm'] = (A[:3, 3] * 100).round(2).tolist()
    M[s] = A; rep[s] = info
import mathutils
for o in [x for x in bpy.data.objects if x.type == 'MESH' and x.name.startswith(NAME)]:
    sd = 'r' if '_R' in o.name else 'l'
    o.data.transform(mathutils.Matrix(M[sd].tolist())); o.data.update()
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE', use_tspace=True,
                             apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
    v = np.array([o.matrix_world @ x.co for x in o.data.vertices])
    if not o.name.endswith(('LOD1', 'LOD2', 'LOD3')): rep[sd]['bbox_cm'] = [(v.min(0) * 100).round(1).tolist(), (v.max(0) * 100).round(1).tolist()]
json.dump(rep, open(os.path.join(D, 'out', 'fit_%s.json' % PIECE.lower()), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, PIECE.lower() + '_knight.blend'))
print('FIT', json.dumps(rep), flush=True)
