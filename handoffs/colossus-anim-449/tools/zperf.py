# zperf.py - key poses for the COLOSSUS performances (SK_Zombie rig, scale-1 metres; the body is x3.9-5.8 in game).
# Signs: pel_y/foot_y > 0 = forward; spine* > 0 = curl forward; head/neck > 0 = nod down; arm_sw > 0 = arm forward/up;
# arm_in: 0 = T-pose, 90 = arms straight down; claw > 0 = curl; twist > 0 = chest to its RIGHT; pel_x > 0 = to its left.
# Rules (RESEARCH.md): anticipation >= 0.4 s, the blow over 5-6 frames (in2), a long settle; the mass keeps going on
# impact (snap overshoot + tremble); deaths hold the last frame and go limp (foot_free).
from zperform import BASE

# replaces A_Attack for the breaker: SAME length 79 frames, the blow on frame 26 (0.87 s) like the old clip. The BP plays
# it at GlobalAnimRateScale 0.45, so in game the wind-up is 1.9 s and the whole smash 5.9 s: giant time.
SMASH = dict(name='CZ_Attack_Smash', length=79/30.0, strike=26/30.0, keys=[
    (0.00, 'smooth', {}),
    (0.30, 'smooth', {'pel_z': -0.14, 'pel_y': -0.03, 'neck': -10, 'head': -4,
                      'arm_sw_L': 60, 'arm_sw_R': 60, 'arm_in_L': 66, 'arm_in_R': 66, 'elbow_L': 40, 'elbow_R': 40,
                      'claw_L': 25, 'claw_R': 25, 'foot_L_z': 0.07, 'foot_L_y': 0.12}),
    (0.50, 'inout', {'foot_L_z': 0.0, 'foot_L_y': 0.26, 'pel_z': -0.09, 'pel_y': -0.07, 'pel_pitch': -8,
                     'spine': -6, 'spine1': -10, 'spine2': -12, 'neck': -14, 'head': -6,
                     'arm_sw_L': 150, 'arm_sw_R': 150, 'arm_in_L': 72, 'arm_in_R': 72, 'elbow_L': 50, 'elbow_R': 50,
                     'hand_L': 15, 'hand_R': 15, 'claw_L': 28, 'claw_R': 28, 'shoulder_L': 8, 'shoulder_R': 8}),
    (0.70, 'linear', {'arm_sw_L': 156, 'arm_sw_R': 156, 'spine2': -13, 'pel_z': -0.08}),      # the held breath
    (26/30.0, 'in2', {'pel_y': 0.14, 'pel_z': -0.26, 'pel_pitch': 18, 'spine': 20, 'spine1': 20, 'spine2': 16, 'neck': 6, 'head': -12,
                      'arm_sw_L': 95, 'arm_sw_R': 95, 'arm_in_L': 76, 'arm_in_R': 76, 'elbow_L': 12, 'elbow_R': 12,
                      'hand_L': -10, 'hand_R': -10, 'claw_L': 32, 'claw_R': 32, 'shoulder_L': -6, 'shoulder_R': -6}),
    (1.00, 'snap', {'pel_z': -0.29, 'spine1': 24, 'tremble': 0.8, 'arm_sw_L': 88, 'arm_sw_R': 88}),                              # the mass keeps dropping
    (1.30, 'out', {'tremble': 0.1, 'pel_z': -0.23, 'spine': 18, 'spine1': 18, 'arm_sw_L': 72, 'arm_sw_R': 72}),
    (1.80, 'smooth', {'tremble': 0.0, 'pel_z': -0.16, 'pel_y': 0.04, 'pel_pitch': 6, 'spine': 12, 'spine1': 12, 'spine2': 9, 'neck': -4, 'head': -8,
                      'arm_sw_L': 12, 'arm_sw_R': 12, 'arm_in_L': 58, 'arm_in_R': 58, 'elbow_L': 30, 'elbow_R': 30, 'hand_L': 0, 'hand_R': 0,
                      'claw_L': 22, 'claw_R': 22, 'foot_L_z': 0.05, 'foot_L_y': 0.12}),
    (2.20, 'smooth', {'foot_L_z': 0.0, 'foot_L_y': 0.0}),
    (79/30.0, 'out', dict(BASE)),
])

# the giant's death: 4.0 s, holds the last frame. The blow lands, it staggers, the knees give, a kneeling beat, then the
# whole mass topples forward onto its face with a ground slam, a rebound, and a last drag of the arm.
DEATH = dict(name='CZ_Death_Colossus', length=4.0, keys=[
    (0.00, 'smooth', {}),
    (0.15, 'snap', {'pel_y': -0.06, 'spine2': -8, 'neck': -18, 'head': -10, 'arm_sw_L': 30, 'arm_sw_R': 30, 'claw_L': -10, 'claw_R': -10,
                    'arm_in_L': 50, 'arm_in_R': 50}),
    (0.70, 'inout', {'pel_z': -0.38, 'pel_y': -0.02, 'pel_pitch': 6, 'spine': 14, 'spine1': 16, 'spine2': 10, 'neck': 0, 'head': 5,
                     'arm_sw_L': 0, 'arm_sw_R': 0, 'elbow_L': 15, 'elbow_R': 15, 'claw_L': 15, 'claw_R': 15, 'arm_in_L': 58, 'arm_in_R': 58}),
    (1.00, 'linear', {'pel_z': -0.45, 'pel_pitch': 10}),                                          # kneeling beat
    (1.90, 'in', {'foot_free': 1.0, 'pel_z': -0.64, 'pel_y': 0.40, 'pel_pitch': 72, 'spine': 10, 'spine1': 8, 'spine2': 4, 'neck': -20,
                  'head_yaw': 20, 'head_roll': 15, 'arm_sw_L': 70, 'arm_sw_R': 70, 'arm_in_L': 45, 'arm_in_R': 45, 'elbow_L': 25, 'elbow_R': 25,
                  'foot_L_y': -0.34, 'foot_R_y': -0.28, 'foot_L_z': 0.10, 'foot_R_z': 0.06}),
    (2.00, 'snap', {'pel_z': -0.72, 'pel_pitch': 78, 'tremble': 0.9, 'foot_L_z': 0.04, 'foot_R_z': 0.02}),                            # the slam
    (2.25, 'out', {'pel_z': -0.68, 'tremble': 0.3}),
    (2.60, 'smooth', {'pel_z': -0.72, 'tremble': 0.0, 'claw_L': 30, 'claw_R': 30}),
    (3.30, 'smooth', {'claw_L': 5, 'claw_R': 5, 'head_roll': 22, 'arm_sw_R': 60, 'elbow_R': 10}),  # the last drag
    (4.00, 'linear', {}),
])

ALL = {'smash': SMASH, 'death': DEATH}
