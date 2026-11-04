"""Línea base de FUERZA BRUTA: recorre los n puntos en cada consulta, O(n).

Sirve como oráculo de correctitud para el quadtree y como baseline de tiempo
en la fase de Experimentación.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from geometry import Point, Rect


def range_query(points: Sequence[Point], rect: Rect) -> List[Point]:
    """Puntos dentro del rectángulo (bordes incluidos)."""
    return [p for p in points if rect.contains_point(p)]


def count_in_range(points: Sequence[Point], rect: Rect) -> int:
    return sum(1 for p in points if rect.contains_point(p))


def density(points: Sequence[Point], rect: Rect) -> float:
    """Densidad = puntos en la región / área de la región."""
    if rect.area <= 0:
        raise ValueError("La región debe tener área > 0")
    return count_in_range(points, rect) / rect.area


def radius_query(points: Sequence[Point], center: Point, r: float) -> List[Point]:
    """Vecinos a distancia <= r de center."""
    if r < 0:
        raise ValueError("r debe ser >= 0")
    r2 = r * r
    return [p for p in points if p.dist_sq(center) <= r2]


def nearest_neighbor(points: Sequence[Point], q: Point,
                     exclude: Optional[Point] = None) -> Optional[Point]:
    """Punto más cercano a q. `exclude` omite ese objeto exacto (identidad),
    útil para buscar el vecino de un punto que ya pertenece al conjunto."""
    best, best_d = None, float("inf")
    for p in points:
        if p is exclude:
            continue
        d = p.dist_sq(q)
        if d < best_d:
            best, best_d = p, d
    return best
