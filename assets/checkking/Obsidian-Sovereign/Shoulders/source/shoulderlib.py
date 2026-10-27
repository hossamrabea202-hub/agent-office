# Obsidian Sovereign pauldron (left, +X), checkking. Reuses the chest helpers with a surface of revolution around the
# upper-arm axis instead of the torso. Frame: the Codex set's world frame (metres, Z up, front = -Y).
#   u: azimuth around the arm axis. 0 = top/outside of the shoulder, +u toward the back (+Y), -u toward the front.
#   h: height along the arm axis (up toward the neck is +), 0 at the shoulder joint.
import sys, os, math
sys.path.insert(0, r'C:\Users\hossam.rabea\checkking-work\chest')
import numpy as np
import chestlib
from chestlib import catmull, smoothstep

TILT = math.radians(30)                           # arm axis tilt from vertical (A-pose, matches the Codex upper arm)
O = np.array([0.232, 0.006, 1.322])               # shoulder joint centre
D = np.array([math.sin(TILT), 0.0, -math.cos(TILT)])  # down the arm
E1 = np.array([math.cos(TILT), 0.0, math.sin(TILT)])  # up-and-out, perpendicular to D
EY = np.array([0.0, 1.0, 0.0])
KY = 1.08                                         # slightly deeper front-to-back than across

HS = [-0.180, -0.140, -0.100, -0.060, -0.020, 0.020, 0.055, 0.082, 0.100, 0.114, 0.124]
RS = [0.094, 0.100, 0.107, 0.114, 0.120, 0.123, 0.116, 0.100, 0.082, 0.062, 0.040]
CAP_LO = -0.040                                   # the keel only runs on the main cap

def radius(u, h):
    r = catmull(HS, RS, h)
    keel = 0.0055 * np.exp(-(u / 0.14) ** 2) * smoothstep(CAP_LO, CAP_LO + 0.03, h) * (1 - smoothstep(0.09, 0.118, h))
    return r + keel

def surf(u, h):
    u = np.asarray(u, float); h = np.asarray(h, float)
    r = radius(u, h)
    c, s = np.cos(u)[..., None], np.sin(u)[..., None]
    return O - D * h[..., None] + r[..., None] * (c * E1 + KY * s * EY)

def surf_n(u, h, d=1e-4):
    p = surf(u, h)
    n = np.cross(surf(u, h + d) - surf(u, h - d), surf(u + d, h) - surf(u - d, h))
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    q = p - O; rad = q - np.sum(q * D, -1, keepdims=True) * D
    flip = np.sign(np.sum(n * rad, -1, keepdims=True))
    return n * np.where(flip == 0, 1, flip)

def axis_out(p):
    """Unit vector from the arm axis to p (outward radial)."""
    q = np.asarray(p) - O; rad = q - np.sum(q * D, -1, keepdims=True) * D
    return rad / np.linalg.norm(rad, axis=-1, keepdims=True)

# route the chest helpers (patch/place) through this surface
chestlib.surf, chestlib.surf_n = surf, surf_n
chestlib.PATCH_CENTER = True
from chestlib import place, patch, tube, ribbon, rivet, mesh_obj  # noqa: E402,F401
