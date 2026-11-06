"""
Suite de Pruebas y Validación para RegionQuadTree vs Matriz 2D de Fuerza Bruta.
Soporta ejecución mediante 'pytest' o 'python -m unittest test_quadtree.py'.
"""

import unittest
import numpy as np
from wormquadtree import RegionQuadTree, CellState

class BruteForceTerrainMatrix:
    """Matriz 2D de fuerza bruta para validación cruzada con el Quadtree."""
    def __init__(self, size: float, resolution: int = 128):
        self.size = float(size)
        self.res = resolution
        self.grid = np.zeros((self.res, self.res), dtype=np.int8)
        
    def generate_terrain(self, surface_y: float):
        cell_size = self.size / self.res
        for y_idx in range(self.res):
            py = (y_idx + 0.5) * cell_size
            if py <= surface_y:
                self.grid[y_idx, :] = 1  # SOLID
            else:
                self.grid[y_idx, :] = 0  # EMPTY

    def carve_circle(self, cx: float, cy: float, radius: float):
        cell_size = self.size / self.res
        for y_idx in range(self.res):
            py = (y_idx + 0.5) * cell_size
            for x_idx in range(self.res):
                px = (x_idx + 0.5) * cell_size
                if (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2:
                    self.grid[y_idx, x_idx] = 0  # EMPTY

    def solid_area(self) -> float:
        solid_count = float(np.sum(self.grid == 1))
        return (solid_count / (self.res * self.res)) * (self.size * self.size)

    def total_area(self) -> float:
        return self.size * self.size

    def destroyed_area(self) -> float:
        return self.total_area() - self.solid_area()


class TestContraFuerzaBruta(unittest.TestCase):
    """Pruebas de equivalencia entre Quadtree y Matriz 2D de Fuerza Bruta."""

    def test_scenarios_equivalence(self):
        scenarios = [
            ("Un solo impacto", [(50.0, 40.0, 15.0)]),
            ("Varios impactos separados", [(25.0, 30.0, 10.0), (75.0, 40.0, 12.0), (50.0, 20.0, 8.0)]),
            ("Impactos cercanos o superpuestos", [(50.0, 40.0, 15.0), (58.0, 42.0, 15.0)]),
            ("Múltiples impactos sobre una misma zona", [(50.0, 40.0, 5.0), (50.0, 40.0, 10.0), (50.0, 40.0, 20.0)]),
            ("Impactos en bordes o esquinas", [(0.0, 0.0, 15.0), (100.0, 0.0, 15.0), (50.0, 0.0, 10.0)]),
            ("Secuencia grande de bombas", [
                (20.0, 20.0, 8.0), (40.0, 30.0, 12.0), (60.0, 25.0, 10.0),
                (80.0, 45.0, 15.0), (35.0, 15.0, 7.0), (70.0, 35.0, 14.0)
            ])
        ]

        U = 100.0
        max_depth = 6
        surface_y = 50.0
        resolution = 128

        for scenario_name, bombs in scenarios:
            with self.subTest(scenario=scenario_name):
                qt = RegionQuadTree(U=U, max_depth=max_depth)
                qt.generate_terrain(surface_y)

                bf = BruteForceTerrainMatrix(size=U, resolution=resolution)
                bf.generate_terrain(surface_y)

                for cx, cy, r in bombs:
                    qt.explosion(cx, cy, r)
                    bf.carve_circle(cx, cy, r)

                qt_destroyed = qt.destroyed_area()
                bf_destroyed = bf.destroyed_area()

                tolerance = (U * U) * 0.04
                self.assertLessEqual(
                    abs(qt_destroyed - bf_destroyed),
                    tolerance,
                    f"Fallo en escenario '{scenario_name}': QuadTree={qt_destroyed:.2f}, BF={bf_destroyed:.2f}"
                )


class TestColapsoDeNodos(unittest.TestCase):
    """Pruebas para verificar el colapso de nodos en el Quadtree."""

    def test_node_collapse_on_complete_destruction(self):
        U = 100.0
        qt = RegionQuadTree(U=U, max_depth=6)
        qt.generate_terrain(surface_y=50.0)

        nodos_iniciales = qt.node_count()
        qt.explosion(cx=50.0, cy=25.0, radius=80.0)
        nodos_despues = qt.node_count()

        self.assertLess(nodos_despues, nodos_iniciales)
        self.assertEqual(qt.root.state, CellState.EMPTY)
        self.assertEqual(qt.root.node_count(), 1)

    def test_terrain_correctness_after_collapse(self):
        U = 100.0
        qt = RegionQuadTree(U=U, max_depth=5)
        qt.generate_terrain(surface_y=50.0)

        qt.explosion(cx=50.0, cy=50.0, radius=20.0)
        nodos_intermedios = qt.node_count()

        qt.explosion(cx=50.0, cy=50.0, radius=100.0)
        nodos_finales = qt.node_count()

        self.assertLess(nodos_finales, nodos_intermedios)
        self.assertEqual(qt.solid_area(), 0.0)
        self.assertEqual(qt.destroyed_area(), U * U)


if __name__ == '__main__':
    unittest.main()
