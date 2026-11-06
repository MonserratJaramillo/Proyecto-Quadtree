"""Clases geométricas base: Point, Segment, Rect y BoundingSquare."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


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
class Segment:
    """Segmento de línea dirigido p1 -> p2 (ideal para proyectiles y raycasting)."""
    p1: Point
    p2: Point


@dataclass(frozen=True)
class Rect:
    """Rectángulo [xmin, xmax] x [ymin, ymax] (cerrado)."""
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

    def intersects_rect(self, other: "Rect") -> bool:
        """Colisión AABB estándar contra otra caja."""
        return not (self.xmax < other.xmin or self.xmin > other.xmax or
                    self.ymax < other.ymin or self.ymin > other.ymax)

    def intersects_segment(self, seg: Segment) -> bool:
        """Intersección de segmento de proyectil usando el algoritmo de Liang-Barsky."""
        dx = seg.p2.x - seg.p1.x
        dy = seg.p2.y - seg.p1.y

        p = [-dx, dx, -dy, dy]
        q = [
            seg.p1.x - self.xmin,
            self.xmax - seg.p1.x,
            seg.p1.y - self.ymin,
            self.ymax - seg.p1.y
        ]

        u1, u2 = 0.0, 1.0

        for pi, qi in zip(p, q):
            if pi == 0:
                if qi < 0:
                    return False
            else:
                t = qi / pi
                if pi < 0:
                    if t > u2:
                        return False
                    if t > u1:
                        u1 = t
                else:
                    if t < u1:
                        return False
                    if t < u2:
                        u2 = t

        return u1 <= u2


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

    def to_rect(self) -> Rect:
        """Convierte la celda cuadrada a un Rect para reutilizar algoritmos AABB."""
        return Rect(self.x, self.y, self.x + self.size, self.y + self.size)

    def contains_xy(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.size
                and self.y <= py <= self.y + self.size)

    def contains(self, p: Point) -> bool:
        return self.contains_xy(p.x, p.y)

    def quadrant_of_xy(self, px: float, py: float) -> str:
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

    def min_dist_sq(self, p: Point) -> float:
        """Distancia mínima al cuadrado desde(p)al cuadrado (0 si está dentro)."""
        dx = max(self.x - p.x, 0.0, p.x - (self.x + self.size))
        dy = max(self.y - p.y, 0.0, p.y - (self.y + self.size))
        return dx * dx + dy * dy

    def circle_relation(self, cx: float, cy: float, radius: float) -> Literal["OUTSIDE", "INSIDE", "INTERSECTS"]:
        """
        Determina la relación geométrica entre el cuadrado y una explosión circular:
        - 'OUTSIDE': El círculo no toca el cuadrado.
        - 'INSIDE': El cuadrado completo queda contenido dentro del cráter.
        - 'INTERSECTS': El borde del cráter corta parcialmente el cuadrado.
        """
        if radius < 0:
            raise ValueError("El radio no puede ser negativo")

        center = Point(cx, cy)
        r2 = radius * radius


        if self.min_dist_sq(center) > r2:
            return "OUTSIDE"


        farthest_x = self.x if abs(self.x - cx) > abs(self.x + self.size - cx) else self.x + self.size
        farthest_y = self.y if abs(self.y - cy) > abs(self.y + self.size - cy) else self.y + self.size

        max_dist_sq = (farthest_x - cx) ** 2 + (farthest_y - cy) ** 2
        if max_dist_sq <= r2:
            return "INSIDE"

        return "INTERSECTS"

    def intersects_aabb(self, rect: Rect) -> bool:
        """Verifica colisión contra la caja de colisión (AABB) de un personaje/objeto."""
        return self.to_rect().intersects_rect(rect)

    def intersects_projectile(self, seg: Segment) -> bool:
        """Verifica si la trayectoria de un proyectil atraviesa esta celda."""
        return self.to_rect().intersects_segment(seg)