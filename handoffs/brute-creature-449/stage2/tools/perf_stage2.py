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
