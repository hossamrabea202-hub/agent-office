# Stage 2 performances (key poses). Times in seconds. Ease names: smooth, in, out, inout, snap, linear (bl_perform.EASES).
# Signs: pel_y/foot_y > 0 = forward; s2..s4 > 0 = curl forward; head/neck > 0 = nod down; arm_sw > 0 = arm forward/up;
# arm_in > 0 = arm toward the body (negative spreads it out); claw > 0 = curl (negative = claws spread);
# twist > 0 = chest turns to the brute's RIGHT; pel_x > 0 = weight to its left.
from bl_perform import BASE

ROAR = dict(name='CR_Roar_Threat', length=3.0, keys=[
    (0.00, 'smooth', {}),
    # gather: sink, curl in, head down, fists
    (0.75, 'inout', {'pel_z': -0.16, 'pel_pitch': 4, 's2': 18, 's3': 17, 's4': 15, 'neck': 4, 'head': -24,
                     'arm_in_L': 30, 'arm_in_R': 30, 'arm_sw_L': 12, 'arm_sw_R': 12, 'elbow_L': 34, 'elbow_R': 34,
                     'claw_L': 28, 'claw_R': 28, 'shoulder_L': 6, 'shoulder_R': 6}),
    # explode up: chest arches, arms flung wide, claws spread, head thrust up and forward
    (1.25, 'out', {'pel_z': -0.03, 'pel_pitch': -6, 's2': 2, 's3': -5, 's4': -9, 'neck': -14, 'head': -4,
                   'arm_in_L': -14, 'arm_in_R': -14, 'arm_sw_L': 38, 'arm_sw_R': 38, 'elbow_L': 24, 'elbow_R': 24,
                   'hand_L': -14, 'hand_R': -14, 'claw_L': -26, 'claw_R': -26, 'shoulder_L': -7, 'shoulder_R': -7}),
    (1.40, 'smooth', {'tremble': 1.0, 'head': -6}),
    (2.15, 'linear', {'tremble': 1.0, 'head_yaw': 7, 'neck_yaw': 4}),
    (2.35, 'smooth', {'tremble': 0.0}),
    (3.00, 'out', dict(BASE)),
])

# replaces FB_A_Attack: same length 2.63 s, the hit lands at 0.87 s (frame 26) like the old clip
SLAM = dict(name='CR_Attack_Slam', length=79/30.0, strike=26/30.0, keys=[
    (0.00, 'smooth', {}),
    (0.25, 'smooth', {'pel_y': -0.04, 'pel_z': -0.12, 's2': 8, 's3': 4, 's4': -2, 'head': -10,
                      'arm_sw_L': 70, 'arm_sw_R': 70, 'elbow_L': 50, 'elbow_R': 50, 'arm_in_L': 12, 'arm_in_R': 12,
                      'claw_L': 12, 'claw_R': 12, 'foot_L_z': 0.07, 'foot_L_y': 0.10}),
    (0.45, 'smooth', {'foot_L_z': 0.0, 'foot_L_y': 0.22}),                         # plants the front foot
    (0.62, 'inout', {'pel_y': -0.07, 'pel_z': -0.06, 's2': -2, 's3': -8, 's4': -12, 'neck': -10, 'head': -12,
                     'arm_sw_L': 150, 'arm_sw_R': 150, 'arm_in_L': 16, 'arm_in_R': 16, 'elbow_L': 70, 'elbow_R': 70,
                     'hand_L': 18, 'hand_R': 18, 'claw_L': 32, 'claw_R': 32, 'shoulder_L': 8, 'shoulder_R': 8}),
    (0.68, 'linear', {'arm_sw_L': 155, 'arm_sw_R': 155, 's4': -13}),               # the held breath before the blow
    (0.87, 'in2', {'pel_y': 0.10, 'pel_z': -0.21, 'pel_pitch': 10, 's2': 22, 's3': 22, 's4': 18, 'neck': 8, 'head': -20,
                  'arm_sw_L': 34, 'arm_sw_R': 34, 'elbow_L': 14, 'elbow_R': 14, 'hand_L': -10, 'hand_R': -10,
                  'claw_L': 36, 'claw_R': 36, 'shoulder_L': -6, 'shoulder_R': -6}),
    (1.02, 'snap', {'pel_z': -0.23, 's3': 25, 'tremble': 0.7}),                    # impact: the mass keeps going down
    (1.30, 'out', {'tremble': 0.0, 'pel_z': -0.18, 's2': 19, 's3': 18, 's4': 14, 'arm_sw_L': 22, 'arm_sw_R': 22}),
    (1.85, 'smooth', {'foot_L_z': 0.06, 'foot_L_y': 0.11}),                        # steps back
    (2.25, 'smooth', {'foot_L_z': 0.0, 'foot_L_y': 0.0}),
    (79/30.0, 'out', dict(BASE)),
])

# replaces FB_ZA_Attack_D: same length 2.0 s, the hit lands at 0.47 s (frame 14)
SWIPE = dict(name='CR_Attack_Swipe', length=60/30.0, strike=14/30.0, keys=[
    (0.00, 'smooth', {}),
    (0.25, 'inout', {'twist': 30, 'pel_yaw': 10, 'pel_x': -0.04, 'head_yaw': 8, 'pel_z': -0.12,
                     'arm_sw_R': 40, 'arm_in_R': -22, 'arm_tw_R': 22, 'elbow_R': 62, 'claw_R': -26, 'hand_R': -10,
                     'arm_sw_L': 10, 'shoulder_R': 8}),
    (0.30, 'linear', {'twist': 33, 'arm_tw_R': 25}),
    (14/30.0, 'in2', {'twist': -30, 'pel_yaw': -12, 'pel_x': 0.04, 'pel_y': 0.06, 'pel_z': -0.15, 's3': 18,
                     'arm_sw_R': 72, 'arm_in_R': 42, 'arm_tw_R': -20, 'elbow_R': 20, 'claw_R': 18, 'hand_R': 12,
                     'arm_sw_L': -20, 'head_yaw': -14, 'neck': 6, 'head': -24, 'shoulder_R': -6}),
    (0.62, 'snap', {'twist': -42, 'arm_in_R': 55, 'arm_sw_R': 46, 'tremble': 0.35}),
    (0.88, 'out', {'tremble': 0.0, 'twist': -20, 'head_yaw': -6}),
    (60/30.0, 'out', dict(BASE)),
])

ALL = {'roar': ROAR, 'slam': SLAM, 'swipe': SWIPE}

# ---------------- stage 3: hits (react from frame 0: 3-frame snap, buckle, late head/arms, heavy recovery) ----------------
def _hit(name, length, snap, settle):
    return dict(name=name, length=length, keys=[(0.00, 'smooth', {}), (0.10, 'snap', snap), (0.24, 'out', settle), (length, 'out', dict(BASE))])

HIT_FRONT = _hit('CR_Hit_Front', 0.9,
    {'pel_y': -0.07, 'pel_z': -0.13, 'pel_pitch': -6, 's2': 6, 's3': -6, 's4': -12, 'neck': -12, 'head': -10,
     'arm_sw_L': 30, 'arm_sw_R': 30, 'arm_in_L': 8, 'arm_in_R': 8, 'elbow_L': 30, 'elbow_R': 30, 'claw_L': -20, 'claw_R': -20},
    {'pel_y': -0.05, 'pel_z': -0.16, 'pel_pitch': -2, 's2': 12, 's3': 6, 's4': 2, 'neck': -4, 'head': -12, 'claw_L': 10, 'claw_R': 10})
HIT_LEFT = _hit('CR_Hit_Left', 0.9,      # struck on its LEFT side: torso shoved to its right, head whips right
    {'pel_x': -0.06, 'pel_z': -0.12, 'pel_roll': -5, 'side': 16, 'twist': -18, 'head_yaw': -16, 'head_roll': 10, 'neck_yaw': -8,
     'arm_in_L': -12, 'arm_sw_L': 25, 'elbow_L': 40, 'claw_L': -24, 'arm_sw_R': -8},
    {'pel_x': -0.03, 'pel_z': -0.15, 'pel_roll': -2, 'side': 6, 'twist': -6, 'head_yaw': -6, 'head_roll': 3, 'neck_yaw': -2, 'claw_L': 12})
HIT_RIGHT = _hit('CR_Hit_Right', 0.9,    # mirror
    {'pel_x': 0.06, 'pel_z': -0.12, 'pel_roll': 5, 'side': -16, 'twist': 18, 'head_yaw': 16, 'head_roll': -10, 'neck_yaw': 8,
     'arm_in_R': -12, 'arm_sw_R': 25, 'elbow_R': 40, 'claw_R': -24, 'arm_sw_L': -8},
    {'pel_x': 0.03, 'pel_z': -0.15, 'pel_roll': 2, 'side': -6, 'twist': 6, 'head_yaw': 6, 'head_roll': -3, 'neck_yaw': 2, 'claw_R': 12})

ALL.update({'hit_front': HIT_FRONT, 'hit_left': HIT_LEFT, 'hit_right': HIT_RIGHT})

# ---------------- stage 3: deaths (hold the last frame; the BP keeps a dead brute on its final pose) ----------------
DEATH_FWD = dict(name='CR_Death_Forward', length=3.0, keys=[   # killing blow, knees buckle, kneel, topple onto the belly, slam, rebound, death twitch
    (0.00, 'smooth', {}),
    (0.15, 'snap', {'pel_y': -0.06, 's4': -10, 'neck': -10, 'head': -14, 'arm_sw_L': 25, 'arm_sw_R': 25, 'claw_L': -20, 'claw_R': -20}),
    (0.55, 'inout', {'pel_z': -0.35, 'pel_y': 0.02, 'pel_pitch': 15, 's2': 18, 's3': 16, 's4': 12, 'neck': 0, 'head': 0,
                     'arm_sw_L': 5, 'arm_sw_R': 5, 'elbow_L': 10, 'elbow_R': 10, 'claw_L': 15, 'claw_R': 15, 'arm_in_L': 15, 'arm_in_R': 15}),
    (0.75, 'linear', {'pel_z': -0.42}),
    (1.30, 'in', {'foot_free': 1.0, 'pel_z': -0.55, 'pel_y': 0.25, 'pel_pitch': 70, 's2': 8, 's3': 6, 's4': 4, 'neck': -25, 'head_yaw': 25, 'head_roll': 20,
                  'arm_sw_L': 60, 'arm_sw_R': 60, 'arm_in_L': -10, 'arm_in_R': -10, 'elbow_L': 20, 'elbow_R': 20}),
    (1.40, 'snap', {'pel_z': -0.60, 'pel_pitch': 75, 'tremble': 0.8}),
    (1.60, 'out', {'pel_z': -0.56, 'tremble': 0.3}),
    (1.90, 'smooth', {'pel_z': -0.60, 'tremble': 0.0, 'neck': -20, 'claw_L': 25, 'claw_R': 25}),
    (2.40, 'smooth', {'claw_L': 5, 'claw_R': 5, 'head_roll': 24}),
    (3.00, 'linear', {}),
])
DEATH_SIDE = dict(name='CR_Death_Side', length=2.6, keys=[     # struck from the left, the legs give, it topples onto its RIGHT side
    (0.00, 'smooth', {}),
    (0.12, 'snap', {'side': 14, 'twist': -12, 'head_yaw': -14, 'pel_x': -0.04}),
    (0.50, 'inout', {'pel_z': -0.25, 'pel_x': -0.10, 'pel_roll': 12, 'side': 18, 'foot_L_x': 0.13, 'foot_free': 0.3, 'arm_in_L': -15, 'arm_in_R': -10}),
    (1.10, 'in', {'pel_z': -0.58, 'pel_x': -0.45, 'pel_roll': 75, 'side': 10, 's2': 10, 'head_roll': 15, 'neck_yaw': 10,
                  'foot_L_x': -0.05, 'foot_L_z': 0.25, 'foot_L_y': 0.10, 'foot_R_x': -0.50, 'foot_R_z': 0.06, 'foot_R_y': 0.18, 'foot_free': 1.0,
                  'arm_in_R': -40, 'arm_sw_L': 40, 'arm_in_L': 10}),
    (1.20, 'snap', {'pel_z': -0.62, 'pel_roll': 80, 'tremble': 0.8, 'foot_L_z': 0.30}),
    (1.40, 'out', {'pel_z': -0.58, 'tremble': 0.3, 'foot_L_z': 0.33}),
    (1.75, 'smooth', {'pel_z': -0.62, 'tremble': 0.0, 'foot_L_z': 0.28, 'claw_L': 25, 'claw_R': 25}),
    (2.60, 'smooth', {'claw_L': 5, 'claw_R': 5}),
])
ALL.update({'death_fwd': DEATH_FWD, 'death_side': DEATH_SIDE})
