"""Clases geométricas base: Point, Rect y BoundingSquare.

Convención de cuadrantes (igual que en el documento del proyecto):
    NE: x > xmid y y > ymid      NW: x <= xmid y y > ymid
    SE: x > xmid y y <= ymid     SW: x <= xmid y y <= ymid
Las regiones son CERRADAS: un punto sobre el borde pertenece a la región.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def dist_sq(self, other: "Point") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def dist(self, other: "Point") -> float:
        return math.sqrt(self.dist_sq(other))


@dataclass(frozen=True)
class Rect:
    """Rectángulo de consulta [xmin, xmax] x [ymin, ymax] (cerrado)."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self):
        if self.xmin > self.xmax or self.ymin > self.ymax:
            raise ValueError("Rect inválido: min debe ser <= max")

    @property
    def area(self) -> float:
        return (self.xmax - self.xmin) * (self.ymax - self.ymin)

    def contains_point(self, p: Point) -> bool:
        return self.xmin <= p.x <= self.xmax and self.ymin <= p.y <= self.ymax


@dataclass(frozen=True)
class BoundingSquare:
    """Cuadrado [x, x+size] x [y, y+size]; (x, y) es la esquina suroeste."""
    x: float
    y: float
    size: float

    def __post_init__(self):
        if self.size <= 0:
            raise ValueError("size debe ser > 0")

    @property
    def xmid(self) -> float:
        return self.x + self.size / 2

    @property
    def ymid(self) -> float:
        return self.y + self.size / 2

    def contains_xy(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.size
                and self.y <= py <= self.y + self.size)

    def contains(self, p: Point) -> bool:
        return self.contains_xy(p.x, p.y)

    def quadrant_of_xy(self, px: float, py: float) -> str:
        """Cuadrante ('NW','NE','SW','SE') al que pertenece el punto."""
        ns = "N" if py > self.ymid else "S"
        ew = "E" if px > self.xmid else "W"
        return ns + ew

    def quadrant_of(self, p: Point) -> str:
        return self.quadrant_of_xy(p.x, p.y)

    def child(self, name: str) -> "BoundingSquare":
        half = self.size / 2
        x0 = self.xmid if name[1] == "E" else self.x
        y0 = self.ymid if name[0] == "N" else self.y
        return BoundingSquare(x0, y0, half)

    def intersects(self, r: Rect) -> bool:
        return (self.x <= r.xmax and r.xmin <= self.x + self.size
                and self.y <= r.ymax and r.ymin <= self.y + self.size)

    def inside(self, r: Rect) -> bool:
        """True si el cuadrado completo cae dentro del rectángulo r."""
        return (r.xmin <= self.x and self.x + self.size <= r.xmax
                and r.ymin <= self.y and self.y + self.size <= r.ymax)

    def min_dist_sq(self, p: Point) -> float:
        """Distancia mínima al cuadrado de p al cuadrado (0 si está dentro)."""
        dx = max(self.x - p.x, 0.0, p.x - (self.x + self.size))
        dy = max(self.y - p.y, 0.0, p.y - (self.y + self.size))
        return dx * dx + dy * dy
