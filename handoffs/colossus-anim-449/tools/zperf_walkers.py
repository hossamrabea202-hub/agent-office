# zperf_walkers.py - key poses for the ordinary zombie walkers (SK_Zombie, scale 1, metres). Feet at GROUND -0.05 like
# the retargeted ZA clips. Same signs as zperf.py. Lengths match the clips they replace so the BP / montage timing holds.
from zperform import BASE
G = -0.05
BASE_W = dict(BASE, pel_z=-0.15, foot_L_z=G, foot_R_z=G, arm_in_L=72, arm_in_R=72, arm_sw_L=20, arm_sw_R=20,
              elbow_L=30, elbow_R=30, claw_L=16, claw_R=16, spine=14, spine1=12, spine2=9, neck=-2, head=0)
def W(**k):
    d = dict(k); return d

# ---- hits: react from frame 0 (a 3-frame snap away from the blow), then a heavy recovery to the base stance ----
HIT_FLINCH = dict(name='ZW_Hit_Flinch', length=20/30.0, keys=[          # replaces ZA_Taking_Damage_A/B/C (0.67 s): a blow to the chest
    (0.00, 'smooth', dict(BASE_W)),
    (0.10, 'snap', W(pel_y=-0.05, pel_z=-0.19, pel_pitch=-5, spine=4, spine1=-6, spine2=-10, neck=-14, head=-6,
                     arm_sw_L=45, arm_sw_R=45, elbow_L=45, elbow_R=45, claw_L=-8, claw_R=-8, shoulder_L=6, shoulder_R=6)),
    (0.30, 'out', W(pel_y=-0.03, pel_z=-0.20, pel_pitch=-1, spine=12, spine1=6, spine2=2, neck=-4, head=-4, arm_sw_L=28, arm_sw_R=28, claw_L=20, claw_R=20)),
    (20/30.0, 'out', dict(BASE_W)),
])
HIT_STAGGER = dict(name='ZW_Hit_Stagger', length=40/30.0, keys=[        # replaces ZA_Taking_Damage_D/E (1.33 s): a heavy blow, a step back
    (0.00, 'smooth', dict(BASE_W)),
    (0.10, 'snap', W(pel_y=-0.08, pel_z=-0.17, pel_pitch=-8, spine=-2, spine1=-10, spine2=-14, neck=-18, head=-10, head_roll=8,
                     arm_sw_L=60, arm_sw_R=55, arm_in_L=55, arm_in_R=58, elbow_L=35, elbow_R=40, claw_L=-10, claw_R=-10, shoulder_L=8, shoulder_R=8)),
    (0.30, 'inout', W(pel_y=-0.16, pel_z=-0.14, foot_R_y=-0.22, foot_R_z=G+0.07, head_yaw=-10)),
    (0.45, 'snap', W(foot_R_y=-0.26, foot_R_z=G, pel_z=-0.22, pel_y=-0.18, spine=10, spine1=2, spine2=-4)),     # the step lands, the weight catches
    (0.80, 'out', W(pel_y=-0.14, pel_z=-0.18, pel_pitch=0, spine=14, spine1=10, spine2=6, neck=-4, head=0, head_roll=2, head_yaw=-3,
                    arm_sw_L=24, arm_sw_R=24, arm_in_L=72, arm_in_R=72, elbow_L=30, elbow_R=30, claw_L=18, claw_R=18, shoulder_L=0, shoulder_R=0)),
    (1.10, 'smooth', W(foot_R_y=-0.10, foot_R_z=G+0.04, pel_y=-0.06)),
    (40/30.0, 'out', dict(BASE_W)),
])
HIT_SIDE = dict(name='ZW_Hit_Side', length=30/30.0, keys=[              # replaces ZA_Taking_Damage_F (1.0 s): struck on its left, twists right
    (0.00, 'smooth', dict(BASE_W)),
    (0.10, 'snap', W(pel_x=-0.06, pel_z=-0.19, pel_roll=-6, side=18, twist=-22, head_yaw=-18, head_roll=12, neck_yaw=-8,
                     arm_in_L=50, arm_sw_L=35, elbow_L=45, claw_L=-10, arm_sw_R=5, shoulder_L=8)),
    (0.32, 'out', W(pel_x=-0.03, pel_z=-0.21, pel_roll=-2, side=6, twist=-8, head_yaw=-6, head_roll=4, neck_yaw=-2, claw_L=20, arm_in_L=68, arm_sw_L=24)),
    (30/30.0, 'out', dict(BASE_W)),
])
HIT_HEAVY = dict(name='ZW_Hit_Heavy', length=60/30.0, keys=[            # replaces A_Hit (2.0 s): knocked down to a knee, climbs back up
    (0.00, 'smooth', dict(BASE_W)),
    (0.10, 'snap', W(pel_y=-0.10, pel_z=-0.18, pel_pitch=-8, spine=-4, spine1=-10, spine2=-12, neck=-18, head=-10,
                     arm_sw_L=60, arm_sw_R=60, arm_in_L=52, arm_in_R=52, elbow_L=30, elbow_R=30, claw_L=-10, claw_R=-10)),
    (0.45, 'in', W(pel_y=-0.18, pel_z=-0.50, pel_pitch=12, spine=16, spine1=12, spine2=6, neck=-6, head=4, foot_R_y=-0.30, foot_R_z=G+0.02,
                   foot_free=0.6, arm_sw_L=35, arm_sw_R=30, elbow_L=20, elbow_R=25, arm_in_L=66, arm_in_R=70)),      # drops onto the right knee
    (0.55, 'snap', W(pel_z=-0.54, tremble=0.5)),
    (0.95, 'smooth', W(pel_z=-0.50, tremble=0.0, head=-2, head_yaw=8, claw_L=22, claw_R=22)),                         # a beat on the knee
    (1.45, 'inout', W(pel_y=-0.08, pel_z=-0.22, pel_pitch=4, foot_R_y=-0.12, foot_R_z=G+0.05, foot_free=0.0, spine=18, spine1=14, spine2=10, arm_sw_L=28, arm_sw_R=28)),
    (1.70, 'smooth', W(foot_R_y=0.0, foot_R_z=G, pel_y=-0.02)),
    (60/30.0, 'out', dict(BASE_W)),
])

# ---- death: replaces A_Death (89 frames, 2.97 s); holds the last frame ----
DEATH_COLLAPSE = dict(name='ZW_Death_Collapse', length=89/30.0, keys=[
    (0.00, 'smooth', dict(BASE_W)),
    (0.12, 'snap', W(pel_y=-0.06, spine1=-8, spine2=-10, neck=-18, head=-10, arm_sw_L=35, arm_sw_R=35, claw_L=-10, claw_R=-10, arm_in_L=55, arm_in_R=55)),
    (0.55, 'inout', W(pel_z=-0.40, pel_y=-0.02, pel_pitch=8, spine=14, spine1=14, spine2=8, neck=2, head=6, arm_sw_L=5, arm_sw_R=5, elbow_L=12, elbow_R=12,
                      arm_in_L=68, arm_in_R=68, claw_L=12, claw_R=12)),                                                   # the legs fold
    (0.80, 'linear', W(pel_z=-0.48, pel_pitch=12)),                                                                        # on the knees
    (1.55, 'in', W(foot_free=1.0, pel_z=-0.66, pel_y=0.36, pel_pitch=74, spine=8, spine1=6, spine2=2, neck=-22, head_yaw=18, head_roll=14,
                   arm_sw_L=65, arm_sw_R=60, arm_in_L=50, arm_in_R=52, elbow_L=20, elbow_R=25, foot_L_y=-0.32, foot_R_y=-0.26, foot_L_z=G+0.10, foot_R_z=G+0.06)),
    (1.65, 'snap', W(pel_z=-0.74, pel_pitch=80, tremble=0.8, foot_L_z=G+0.03, foot_R_z=G+0.02)),                            # face down
    (1.90, 'out', W(pel_z=-0.71, tremble=0.3)),
    (2.25, 'smooth', W(pel_z=-0.74, tremble=0.0, claw_L=28, claw_R=28)),
    (2.70, 'smooth', W(claw_L=6, claw_R=6, head_roll=20, arm_sw_R=52)),
    (89/30.0, 'linear', {}),
])

# ---- attacks: the strike frames are kept (the BP applies damage on a timer tuned to the old clips) ----
ATTACK_CLAW = dict(name='ZW_Attack_Claw', length=79/30.0, strike=26/30.0, keys=[   # replaces A_Attack (79 f, blow at 26): a lunging two-arm rake
    (0.00, 'smooth', dict(BASE_W)),
    (0.35, 'inout', W(pel_y=-0.06, pel_z=-0.18, pel_pitch=-4, spine=6, spine1=0, spine2=-6, neck=-12, head=-6, twist=22, pel_yaw=8,
                      arm_sw_L=-45, arm_sw_R=10, arm_in_L=40, arm_in_R=70, elbow_L=50, elbow_R=35, claw_L=-16, claw_R=-18, hand_L=-10, hand_R=-12,
                      shoulder_L=6, shoulder_R=8, foot_L_y=0.08, foot_L_z=G+0.05)),
    (0.62, 'linear', W(arm_sw_L=-50, spine2=-8, foot_L_y=0.22, foot_L_z=G)),                                               # the held beat, the front foot plants
    (26/30.0, 'in2', W(pel_y=0.16, pel_z=-0.24, pel_pitch=16, spine=22, spine1=20, spine2=14, neck=4, head=-10, twist=-20, pel_yaw=-8,
                       arm_sw_L=80, arm_sw_R=20, arm_in_L=74, arm_in_R=76, elbow_L=15, elbow_R=30, claw_L=30, claw_R=30, hand_L=10, hand_R=12,
                       shoulder_L=-4, shoulder_R=-6)),
    (1.00, 'snap', W(twist=-26, pel_z=-0.26, tremble=0.4)),
    (1.30, 'out', W(tremble=0.0, twist=-12, pel_z=-0.22, arm_sw_L=55, arm_sw_R=22)),
    (1.85, 'smooth', W(pel_y=0.06, pel_z=-0.17, pel_pitch=4, spine=16, spine1=12, spine2=8, twist=0, pel_yaw=0, neck=-4, head=-2,
                       arm_sw_L=24, arm_sw_R=24, arm_in_L=72, arm_in_R=72, elbow_L=30, elbow_R=30, claw_L=18, claw_R=18, hand_L=0, hand_R=0, foot_L_y=0.10, foot_L_z=G+0.04)),
    (2.25, 'smooth', W(foot_L_y=0.0, foot_L_z=G, pel_y=0.0)),
    (79/30.0, 'out', dict(BASE_W)),
])
ATTACK_BITE = dict(name='ZW_Attack_Bite', length=60/30.0, strike=16/30.0, keys=[   # replaces ZA_Attack_D (60 f, blow at 16): a grab-and-bite lunge
    (0.00, 'smooth', dict(BASE_W)),
    (0.22, 'inout', W(pel_y=-0.08, pel_z=-0.20, pel_pitch=-6, spine=4, spine1=-4, spine2=-8, neck=-16, head=-10,
                      arm_sw_L=30, arm_sw_R=30, arm_in_L=66, arm_in_R=66, elbow_L=70, elbow_R=70, claw_L=-14, claw_R=-14, hand_L=-10, hand_R=-10, shoulder_L=8, shoulder_R=8)),
    (0.36, 'linear', W(arm_sw_L=26, arm_sw_R=26, spine2=-9)),
    (16/30.0, 'in2', W(pel_y=0.18, pel_z=-0.22, pel_pitch=14, spine=18, spine1=16, spine2=12, neck=14, head=16,
                       arm_sw_L=55, arm_sw_R=55, arm_in_L=84, arm_in_R=84, elbow_L=40, elbow_R=40, claw_L=34, claw_R=34, hand_L=8, hand_R=8, shoulder_L=-4, shoulder_R=-4,
                       foot_L_y=0.24, foot_L_z=G)),
    (0.66, 'snap', W(pel_y=0.20, neck=18, head=20, tremble=0.5, elbow_L=45, elbow_R=45)),                                 # the bite clamps
    (0.95, 'out', W(tremble=0.0, neck=6, head=8, pel_z=-0.20)),
    (1.45, 'smooth', W(pel_y=0.06, pel_z=-0.17, pel_pitch=4, spine=15, spine1=12, spine2=9, neck=-2, head=0, arm_sw_L=26, arm_sw_R=26,
                       arm_in_L=72, arm_in_R=72, elbow_L=30, elbow_R=30, claw_L=18, claw_R=18, hand_L=0, hand_R=0, shoulder_L=0, shoulder_R=0, foot_L_y=0.10, foot_L_z=G+0.04)),
    (1.75, 'smooth', W(foot_L_y=0.0, foot_L_z=G, pel_y=0.0)),
    (60/30.0, 'out', dict(BASE_W)),
])

ALL = {'hit_flinch': HIT_FLINCH, 'hit_stagger': HIT_STAGGER, 'hit_side': HIT_SIDE, 'hit_heavy': HIT_HEAVY,
       'death_collapse': DEATH_COLLAPSE, 'attack_claw': ATTACK_CLAW, 'attack_bite': ATTACK_BITE}
