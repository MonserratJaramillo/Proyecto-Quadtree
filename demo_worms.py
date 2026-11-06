"""
Demo, Benchmarking y Comparación de Rendimiento:
Quadtree vs Matriz 2D de Fuerza Bruta
"""

import time
import tracemalloc
import random
import numpy as np
from wormquadtree import RegionQuadTree

class BruteForceTerrainMatrix:
    """Matriz 2D de fuerza bruta para benchmarks de rendimiento."""
    def __init__(self, size: float, resolution: int = 128):
        self.size = float(size)
        self.res = resolution
        self.grid = np.zeros((self.res, self.res), dtype=np.int8)
        
    def generate_terrain(self, surface_y: float):
        cell_size = self.size / self.res
        for y_idx in range(self.res):
            py = (y_idx + 0.5) * cell_size
            if py <= surface_y:
                self.grid[y_idx, :] = 1
            else:
                self.grid[y_idx, :] = 0

    def carve_circle(self, cx: float, cy: float, radius: float):
        cell_size = self.size / self.res
        for y_idx in range(self.res):
            py = (y_idx + 0.5) * cell_size
            for x_idx in range(self.res):
                px = (x_idx + 0.5) * cell_size
                if (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2:
                    self.grid[y_idx, x_idx] = 0


def render_ascii_terrain(qt: RegionQuadTree, cols: int = 40, rows: int = 15):
    """Visualizador opcional del terreno en consola ASCII."""
    grid = [[" " for _ in range(cols)] for _ in range(rows)]
    step_x = qt.U / cols
    step_y = qt.U / rows

    for r in range(rows):
        py = (rows - 1 - r) * step_y + step_y / 2
        for c in range(cols):
            px = c * step_x + step_x / 2
            # Consultar en las hojas del QuadTree
            is_solid = False
            for leaf in qt.leaves():
                if leaf.state.name == "SOLID" and leaf.boundary.contains_xy(px, py):
                    is_solid = True
                    break
            grid[r][c] = "#" if is_solid else "."
            
    return "\n".join("".join(row) for row in grid)


def run_benchmark():
    U = 200.0
    surface_y = 100.0
    bomb_counts = [10, 100, 500, 1000]

    random.seed(42)
    scenarios = {
        count: [(random.uniform(20, 180), random.uniform(20, 180), random.uniform(5, 15)) for _ in range(count)]
        for count in bomb_counts
    }

    print("==========================================================================")
    print("        BENCHMARK & DEMO: QUADTREE VS MATRIZ 2D FUERZA BRUTA             ")
    print("==========================================================================")
    print(f"{'Método':<22} | {'Bombas':<8} | {'Tiempo (s)':<12} | {'Memoria (KiB)':<14}")
    print("--------------------------------------------------------------------------")

    for count, bombs in scenarios.items():
        # 1. Quadtree Benchmark
        tracemalloc.start()
        start_t = time.perf_counter()

        qt = RegionQuadTree(U=U, max_depth=6)
        qt.generate_terrain(surface_y)
        for cx, cy, r in bombs:
            qt.explosion(cx, cy, r)

        qt_time = time.perf_counter() - start_t
        _, qt_mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # 2. Fuerza Bruta Benchmark
        tracemalloc.start()
        start_t = time.perf_counter()

        bf = BruteForceTerrainMatrix(size=U, resolution=128)
        bf.generate_terrain(surface_y)
        for cx, cy, r in bombs:
            bf.carve_circle(cx, cy, r)

        bf_time = time.perf_counter() - start_t
        _, bf_mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Formato de métricas
        qt_mem_kib = qt_mem_peak / 1024
        bf_mem_kib = bf_mem_peak / 1024

        speedup = bf_time / qt_time if qt_time > 0 else 0

        print(f"{'Quadtree':<22} | {count:<8} | {qt_time:<12.6f} | {qt_mem_kib:<14.2f}")
        print(f"{'Fuerza Bruta (128x128)':<22} | {count:<8} | {bf_time:<12.6f} | {bf_mem_kib:<14.2f}")
        print(f"--> Quadtree es {speedup:.2f}x más rápido ({((bf_time - qt_time) / bf_time) * 100:.1f}% menor tiempo)")
        print("--------------------------------------------------------------------------")

    print("\n--- DEMO: Visualización ASCII del terreno tras 3 explosiones ---")
    demo_qt = RegionQuadTree(U=100.0, max_depth=5)
    demo_qt.generate_terrain(50.0)
    demo_qt.explosion(30.0, 40.0, 15.0)
    demo_qt.explosion(70.0, 45.0, 12.0)
    demo_qt.explosion(50.0, 30.0, 10.0)
    print(render_ascii_terrain(demo_qt))
    print(f"Área Sólida Restante: {demo_qt.solid_area():.2f} / {demo_qt.total_area():.2f}")


if __name__ == "__main__":
    run_benchmark()
