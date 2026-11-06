from __future__ import annotations

import math
import random
import sys
import time
import tracemalloc
from typing import Callable, Dict, List, Tuple


class BruteForceTerrain:

    def __init__(self, width: int, height: int, solid: bool = False) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width y height deben ser positivos")
        self.width = width
        self.height = height
        self.grid: List[List[bool]] = [[solid] * width for _ in range(height)]
        self._initial_solid = width * height if solid else 0

    @classmethod
    def lower_half_solid(cls, width: int, height: int) -> "BruteForceTerrain":
        terrain = cls(width, height, solid=False)
        for y in range(height // 2, height):
            for x in range(width):
                terrain.grid[y][x] = True
        terrain.reset_baseline()
        return terrain

    def reset_baseline(self) -> None:
        self._initial_solid = self.solid_area()

    def copy(self) -> "BruteForceTerrain":
        other = BruteForceTerrain(self.width, self.height)
        other.grid = [row[:] for row in self.grid]
        other._initial_solid = self._initial_solid
        return other

    def carve_circle(self, cx: float, cy: float, radius: float,
                     center_offset: float = 0.0) -> int:
        if radius < 0:
            raise ValueError("radius no puede ser negativo")
        r2 = radius * radius

        x_min = max(0, math.floor(cx - radius - center_offset))
        x_max = min(self.width - 1, math.ceil(cx + radius - center_offset))
        y_min = max(0, math.floor(cy - radius - center_offset))
        y_max = min(self.height - 1, math.ceil(cy + radius - center_offset))

        destroyed = 0
        for y in range(y_min, y_max + 1):
            dy = (y + center_offset) - cy
            row = self.grid[y]
            for x in range(x_min, x_max + 1):
                dx = (x + center_offset) - cx
                if row[x] and dx * dx + dy * dy <= r2:
                    row[x] = False
                    destroyed += 1
        return destroyed

    def solid_area(self) -> int:
        total = 0
        for row in self.grid:
            for cell in row:
                if cell:
                    total += 1
        return total

    def is_solid(self, x: float, y: float) -> bool:
        px, py = math.floor(x), math.floor(y)
        if px < 0 or py < 0 or px >= self.width or py >= self.height:
            return False
        return self.grid[py][px]

    def destroyed_percentage(self) -> float:
        if self._initial_solid == 0:
            return 0.0
        remaining = self.solid_area()
        return 100.0 * (self._initial_solid - remaining) / self._initial_solid

    def mismatches(self, query: Callable[[int, int], bool]
                   ) -> List[Tuple[int, int, bool, bool]]:
        diffs = []
        for y in range(self.height):
            for x in range(self.width):
                expected = self.grid[y][x]
                got = bool(query(x, y))
                if expected != got:
                    diffs.append((x, y, expected, got))
        return diffs

    def to_ascii(self, solid_char: str = "#", air_char: str = ".") -> str:
        return "\n".join(
            "".join(solid_char if c else air_char for c in row)
            for row in self.grid
        )


def _self_test() -> None:
    t = BruteForceTerrain(16, 16, solid=False)
    assert t.carve_circle(8, 8, 3) == 0
    assert t.destroyed_percentage() == 0.0

    t = BruteForceTerrain(16, 16, solid=True)
    assert t.carve_circle(5, 5, 0) == 1
    assert not t.is_solid(5, 5) and t.is_solid(6, 5)

    for r, expected in [(1, 5), (2, 13), (3, 29)]:
        t = BruteForceTerrain(32, 32, solid=True)
        assert t.carve_circle(16, 16, r) == expected, (r, expected)
        assert t.solid_area() == 32 * 32 - expected

    t = BruteForceTerrain(16, 16, solid=True)
    t.carve_circle(5, 5, 3)
    assert not t.is_solid(8, 5) and t.is_solid(9, 5)

    t = BruteForceTerrain(32, 32, solid=True)
    t.carve_circle(16, 16, 5)
    assert t.carve_circle(16, 16, 3) == 0

    t = BruteForceTerrain(8, 8, solid=True)
    assert t.carve_circle(-1, -1, 2) == 1
    assert t.carve_circle(100, 100, 3) == 0

    t = BruteForceTerrain.lower_half_solid(8, 8)
    assert t.solid_area() == 32
    assert not t.is_solid(3, 3) and t.is_solid(3, 4)
    assert t.carve_circle(4, 4, 1) == 4
    assert t.destroyed_percentage() == 12.5

    ref = t.copy()
    assert t.mismatches(lambda x, y: ref.grid[y][x]) == []
    assert len(t.mismatches(lambda x, y: True)) == 8 * 8 - t.solid_area()

    print("brute_force.py: todas las pruebas pasaron")


Bomb = Tuple[int, int, int]


def random_bombs(width: int, height: int, n: int, r_min: int, r_max: int,
                 seed: int = 0) -> List[Bomb]:
    rng = random.Random(seed)
    return [(rng.randrange(width), rng.randrange(height), rng.randint(r_min, r_max))
            for _ in range(n)]


def run_bombs(terrain: BruteForceTerrain, bombs: List[Bomb]) -> None:
    for cx, cy, r in bombs:
        terrain.carve_circle(cx, cy, r)


def benchmark(width: int, height: int, bombs: List[Bomb]) -> Dict[str, float]:
    tracemalloc.start()
    terrain = BruteForceTerrain.lower_half_solid(width, height)
    memory_bytes = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    start = time.perf_counter()
    run_bombs(terrain, bombs)
    elapsed = time.perf_counter() - start

    return {
        "time_ms": elapsed * 1000,
        "memory_kb": memory_bytes / 1024,
        "destroyed_pct": terrain.destroyed_percentage(),
    }


Point = Tuple[float, float]


def _xy(p):
    if hasattr(p, "x") and hasattr(p, "y"):
        return p.x, p.y
    return p[0], p[1]


def _dentro(region, p) -> bool:
    for nombre in ("contains", "contains_point"):
        metodo = getattr(region, nombre, None)
        if callable(metodo):
            return bool(metodo(p))
    x, y, w, h = region
    px, py = _xy(p)
    return x <= px <= x + w and y <= py <= y + h


def _area(region) -> float:
    area = getattr(region, "area", None)
    if area is not None:
        return area() if callable(area) else area
    _, _, w, h = region
    return w * h


def range_query(points, region) -> List:
    result = []
    for p in points:
        if _dentro(region, p):
            result.append(p)
    return result


def count_in_region(points, region) -> int:
    total = 0
    for p in points:
        if _dentro(region, p):
            total += 1
    return total


def density(points, region) -> float:
    area = _area(region)
    if area == 0:
        raise ValueError("el área de la región es cero")
    return count_in_region(points, region) / area


def nearest_neighbor(points, query, exclude_self: bool = False):
    qx, qy = _xy(query)
    best = None
    best_key = None
    for p in points:
        px, py = _xy(p)
        if exclude_self and (px, py) == (qx, qy):
            continue
        key = ((px - qx) ** 2 + (py - qy) ** 2, px, py)
        if best_key is None or key < best_key:
            best, best_key = p, key
    return best


def _self_test_puntos() -> None:
    pts = [(1, 1), (2, 2), (5, 5), (3, 1), (1, 3)]
    region = (0, 0, 3, 3)

    assert range_query(pts, region) == [(1, 1), (2, 2), (3, 1), (1, 3)]
    assert count_in_region(pts, region) == 4
    assert count_in_region(pts, (10, 10, 1, 1)) == 0
    assert abs(density(pts, region) - 4 / 9) < 1e-12

    try:
        density(pts, (0, 0, 0, 5))
        raise AssertionError("density debía lanzar ValueError")
    except ValueError:
        pass

    assert nearest_neighbor(pts, (2, 2)) == (2, 2)
    assert nearest_neighbor(pts, (2, 2), exclude_self=True) == (1, 1)
    assert nearest_neighbor([(1, 0), (0, 1)], (0, 0)) == (0, 1)
    assert nearest_neighbor([], (0, 0)) is None
    assert nearest_neighbor([(2, 2)], (2, 2), exclude_self=True) is None

    class Caja:
        def contains(self, p):
            return 0 <= p[0] < 2 and 0 <= p[1] < 2

        def area(self):
            return 4

    assert range_query(pts, Caja()) == [(1, 1)]
    assert density(pts, Caja()) == 0.25

    class P:
        def __init__(self, x, y):
            self.x, self.y = x, y

    a, b = P(0, 0), P(3, 4)
    assert nearest_neighbor([b, a], P(1, 0)) is a
    assert range_query([a, b], (0, 0, 1, 1)) == [a]

    print("brute_force.py: pruebas de puntos pasaron")


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(1_000_000)
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    n_bombs = int(sys.argv[4]) if len(sys.argv) > 4 else 4

    _self_test()
    _self_test_puntos()

    bombs = random_bombs(width, height, n_bombs,
                         max(1, width // 24), max(2, width // 9), seed)
    stats = benchmark(width, height, bombs)

    terrain = BruteForceTerrain.lower_half_solid(width, height)
    initial_solid = terrain.solid_area()

    print(f"\nSemilla: {seed}")
    print(f"Mapa: {width}x{height} píxeles")
    print(f"Tierra inicial: {initial_solid} píxeles (mitad de abajo)")

    show_map = width <= 100 and height <= 40

    if show_map:
        print("\nMapa inicial:")
        print(terrain.to_ascii())

    print("\nBombas (x, y, radio):")
    for i, (cx, cy, r) in enumerate(bombs[:10], 1):
        print(f"  {i}. ({cx}, {cy}) radio {r}")
    if len(bombs) > 10:
        print(f"  ... y {len(bombs) - 10} más")

    run_bombs(terrain, bombs)

    if show_map:
        print("\nMapa después de las bombas:")
        print(terrain.to_ascii())
    else:
        print("\n(El mapa es muy grande para dibujarlo en consola.)")

    destroyed_px = initial_solid - terrain.solid_area()
    print(f"\nTiempo: {stats['time_ms']:.3f} ms")
    print(f"Memoria del mapa: {stats['memory_kb']:.1f} KB")
    print(f"Destruido: {destroyed_px} de {initial_solid} píxeles "
          f"({terrain.destroyed_percentage():.2f} %)")