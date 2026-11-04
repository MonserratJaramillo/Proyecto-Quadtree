"""Quadtree de puntos: QuadTreeNode + QuadTree.

Cubre: construcción (insert), consulta de rango/densidad/radio, vecino más
cercano, búsqueda de vecinos por celda (subir al ancestro y bajar, Teorema 14.2)
y balanceo 2:1 (extensión del Cap. 14).
"""
from __future__ import annotations

import heapq
import math
from itertools import count
from typing import Dict, Iterable, Iterator, List, Optional

from geometry import BoundingSquare, Point, Rect

QUADRANTS = ("NW", "NE", "SW", "SE")
_FLIP = {"N": "S", "S": "N", "E": "W", "W": "E"}


class QuadTreeNode:
    def __init__(self, boundary: BoundingSquare, capacity: int, depth: int,
                 max_depth: int, parent: Optional["QuadTreeNode"] = None,
                 quadrant: Optional[str] = None):
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.parent = parent
        self.quadrant = quadrant          # posición dentro del padre
        self.points: List[Point] = []     # solo se usan en hojas
        self.children: Dict[str, QuadTreeNode] = {}
        self.n_points = 0                 # puntos en todo el subárbol

    @property
    def divided(self) -> bool:
        return bool(self.children)

    # ---- construcción -------------------------------------------------
    def subdivide(self) -> None:
        """Divide la hoja en NW, NE, SW, SE y redistribuye sus puntos."""
        if self.divided:
            return
        for name in QUADRANTS:
            self.children[name] = QuadTreeNode(
                self.boundary.child(name), self.capacity, self.depth + 1,
                self.max_depth, parent=self, quadrant=name)
        old, self.points = self.points, []
        for p in old:
            self.children[self.boundary.quadrant_of(p)].insert(p)

    def insert(self, p: Point) -> bool:
        if not self.boundary.contains(p):
            return False
        if not self.divided:
            if len(self.points) < self.capacity or self.depth >= self.max_depth:
                self.points.append(p)
                self.n_points += 1
                return True
            self.subdivide()
        self.n_points += 1
        return self.children[self.boundary.quadrant_of(p)].insert(p)

    # ---- vecinos por celda (sin usar coordenadas) -----------------------
    def find_neighbor(self, direction: str) -> Optional["QuadTreeNode"]:
        """Vecino en 'N','S','E','W' de tamaño igual o mayor (None si no hay).
        Sube hasta un ancestro común y baja por el cuadrante espejo: O(d+1)."""
        if self.parent is None:
            return None
        q = self.quadrant
        axis = 0 if direction in "NS" else 1
        if q[axis] == _FLIP[direction]:               # el hermano ya está allí
            return self.parent.children[q[:axis] + direction + q[axis + 1:]]
        n = self.parent.find_neighbor(direction)
        if n is None or not n.divided:
            return n
        mirror = q[:axis] + _FLIP[q[axis]] + q[axis + 1:]
        return n.children[mirror]


class QuadTree:
    def __init__(self, U: float, capacity: int = 1,
                 max_depth: Optional[int] = None):
        if capacity < 1:
            raise ValueError("capacity debe ser >= 1")
        if max_depth is None:                          # d = log2 U
            max_depth = max(0, math.ceil(math.log2(U)))
        self.U = U
        self.capacity = capacity
        self.max_depth = max_depth
        self.root = QuadTreeNode(BoundingSquare(0, 0, U), capacity, 0, max_depth)

    @classmethod
    def from_points(cls, points: Iterable[Point], U: float, capacity: int = 1,
                    max_depth: Optional[int] = None) -> "QuadTree":
        qt = cls(U, capacity, max_depth)
        qt.insert_many(points)
        return qt

    def __len__(self) -> int:
        return self.root.n_points

    # ---- inserción ------------------------------------------------------
    def insert(self, p: Point) -> bool:
        return self.root.insert(p)

    def insert_many(self, points: Iterable[Point]) -> int:
        return sum(1 for p in points if self.insert(p))

    # ---- consultas ------------------------------------------------------
    def range_query(self, rect: Rect) -> List[Point]:
        out: List[Point] = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.n_points == 0 or not node.boundary.intersects(rect):
                continue                               # poda
            if node.divided:
                stack.extend(node.children.values())
            else:
                out.extend(p for p in node.points if rect.contains_point(p))
        return out

    def count_in_range(self, rect: Rect) -> int:
        total = 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.n_points == 0 or not node.boundary.intersects(rect):
                continue
            if node.boundary.inside(rect):             # subárbol completo
                total += node.n_points
            elif node.divided:
                stack.extend(node.children.values())
            else:
                total += sum(1 for p in node.points if rect.contains_point(p))
        return total

    def density(self, rect: Rect) -> float:
        if rect.area <= 0:
            raise ValueError("La región debe tener área > 0")
        return self.count_in_range(rect) / rect.area

    def radius_query(self, center: Point, r: float) -> List[Point]:
        if r < 0:
            raise ValueError("r debe ser >= 0")
        r2, out = r * r, []
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.n_points == 0 or node.boundary.min_dist_sq(center) > r2:
                continue
            if node.divided:
                stack.extend(node.children.values())
            else:
                out.extend(p for p in node.points if p.dist_sq(center) <= r2)
        return out

    def nearest_neighbor(self, q: Point,
                         exclude: Optional[Point] = None) -> Optional[Point]:
        """Búsqueda best-first: visita celdas por distancia mínima creciente."""
        best, best_d = None, float("inf")
        tie = count()
        heap = [(self.root.boundary.min_dist_sq(q), next(tie), self.root)]
        while heap:
            d, _, node = heapq.heappop(heap)
            if d >= best_d:
                break
            if node.divided:
                for ch in node.children.values():
                    if ch.n_points:
                        heapq.heappush(
                            heap, (ch.boundary.min_dist_sq(q), next(tie), ch))
            else:
                for p in node.points:
                    if p is exclude:
                        continue
                    dd = p.dist_sq(q)
                    if dd < best_d:
                        best, best_d = p, dd
        return best

    # ---- navegación y estadísticas ---------------------------------------
    def leaf_at(self, px: float, py: float) -> Optional[QuadTreeNode]:
        """Hoja que contiene (px, py); None si cae fuera del dominio."""
        node = self.root
        if not node.boundary.contains_xy(px, py):
            return None
        while node.divided:
            node = node.children[node.boundary.quadrant_of_xy(px, py)]
        return node

    def neighbor(self, node: QuadTreeNode, direction: str) -> Optional[QuadTreeNode]:
        return node.find_neighbor(direction)

    def leaves(self) -> Iterator[QuadTreeNode]:
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.divided:
                stack.extend(node.children.values())
            else:
                yield node

    def depth(self) -> int:
        return max(leaf.depth for leaf in self.leaves())

    def node_count(self) -> int:
        total, stack = 0, [self.root]
        while stack:
            node = stack.pop()
            total += 1
            stack.extend(node.children.values())
        return total

    # ---- balanceo 2:1 -----------------------------------------------------
    @staticmethod
    def _probes(b: BoundingSquare):
        """8 puntos justo fuera de la celda: 4 aristas + 4 esquinas."""
        x, y, s = b.x, b.y, b.size
        d, m = s / 4, s / 2
        return [(x - d, y + m), (x + s + d, y + m), (x + m, y - d),
                (x + m, y + s + d), (x - d, y - d), (x + s + d, y - d),
                (x - d, y + s + d), (x + s + d, y + s + d)]

    def balance(self) -> int:
        """Divide hojas demasiado grandes hasta que celdas que comparten arista
        o vértice no difieran en tamaño por más de 2. Devuelve # de divisiones."""
        splits, changed = 0, True
        while changed:
            changed = False
            for leaf in list(self.leaves()):
                if leaf.divided:                       # ya dividida en esta pasada
                    continue
                for px, py in self._probes(leaf.boundary):
                    other = self.leaf_at(px, py)
                    if (other is not None and not other.divided
                            and other.boundary.size > 2 * leaf.boundary.size):
                        other.subdivide()
                        splits += 1
                        changed = True
        return splits

    def is_balanced(self) -> bool:
        for leaf in self.leaves():
            for px, py in self._probes(leaf.boundary):
                other = self.leaf_at(px, py)
                if other is not None and other.boundary.size > 2 * leaf.boundary.size:
                    return False
        return True
