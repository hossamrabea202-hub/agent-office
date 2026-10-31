# Obsidian Sovereign gauntlet (left, +X), checkking. Every part (hand, cuff, each finger joint, thumb) is a surface of
# revolution around its own axis; use(ax) routes the chest's patch/place helpers through that surface.
# Frame: the Codex set's world frame (metres, Z up, front = -Y). Hand hangs straight down, back of hand toward -Y,
# thumb toward the body (-X), as in the Codex gauntlet.
import sys, math
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import numpy as np
import chestlib
from chestlib import catmull
chestlib.PATCH_CENTER = True

def unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)

class Axial:
    """surf(u, h) = O - D*h + r(h) * (cos u * E1 + k(h) * sin u * E2).  D points 'down' the part (toward the tip),
    h grows back up toward O. E1 is u = 0 (the back / outside), E2 = (-D) x E1."""
    def __init__(self, O, D, E1, hs, rs, ks=None):
        self.O = np.asarray(O, float); self.D = unit(D)
        e1 = np.asarray(E1, float); e1 = e1 - (e1 @ self.D) * self.D; self.E1 = unit(e1)
        self.E2 = np.cross(-self.D, self.E1)
        self.hs, self.rs = list(hs), list(rs); self.ks = list(ks) if ks is not None else [1.0] * len(hs)
    def r(self, h): return catmull(self.hs, self.rs, h)
    def k(self, h): return catmull(self.hs, self.ks, h)
    def surf(self, u, h):
        u = np.asarray(u, float); h = np.asarray(h, float)
        c, s = np.cos(u)[..., None], np.sin(u)[..., None]
        return self.O - self.D * h[..., None] + self.r(h)[..., None] * (c * self.E1 + self.k(h)[..., None] * s * self.E2)
    def surf_n(self, u, h, d=1e-5):
        p = self.surf(u, h)
        n = np.cross(self.surf(u, h + d) - self.surf(u, h - d), self.surf(u + d, h) - self.surf(u - d, h))
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
        q = p - self.O; rad = q - np.sum(q * self.D, -1, keepdims=True) * self.D
        flip = np.sign(np.sum(n * rad, -1, keepdims=True))
        return n * np.where(flip == 0, 1, flip)
    def at(self, u, h, off=0.0):
        return self.surf(u, h) + self.surf_n(u, h) * off
    def u_for_x(self, h, dx):
        """azimuth whose point sits dx along E2 from the axis (for placing things over a given finger)."""
        return math.asin(max(-1.0, min(1.0, dx / float(self.r(h) * self.k(h)))))

def use(ax):
    chestlib.surf, chestlib.surf_n = ax.surf, ax.surf_n

from chestlib import place, patch, tube, ribbon, rivet, mesh_obj  # noqa: E402,F401

