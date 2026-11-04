"""Generadores de datasets sintéticos (semilla fija => reproducible)."""
from __future__ import annotations

import math
import random
from typing import List

from geometry import Point, Rect


def uniform_points(n: int, U: float, seed: int = 0) -> List[Point]:
    rng = random.Random(seed)
    return [Point(rng.uniform(0, U), rng.uniform(0, U)) for _ in range(n)]


def clustered_points(n: int, U: float, n_clusters: int = 5,
                     sigma_frac: float = 0.03, seed: int = 0) -> List[Point]:
    """Clusters gaussianos; las coordenadas se recortan a [0, U]."""
    rng = random.Random(seed)
    centers = [(rng.uniform(0, U), rng.uniform(0, U)) for _ in range(n_clusters)]
    sigma = U * sigma_frac
    clamp = lambda v: min(max(v, 0.0), float(U))
    pts = []
    for _ in range(n):
        cx, cy = rng.choice(centers)
        pts.append(Point(clamp(rng.gauss(cx, sigma)), clamp(rng.gauss(cy, sigma))))
    return pts


def random_query_rect(U: float, area_fraction: float,
                      rng: random.Random) -> Rect:
    """Rectángulo cuadrado con ~area_fraction del área del dominio."""
    side = U * math.sqrt(area_fraction)
    x0 = rng.uniform(0, U - side)
    y0 = rng.uniform(0, U - side)
    return Rect(x0, y0, x0 + side, y0 + side)
