"""Demo rápida: verifica igualdad de resultados y compara tiempos (n pequeño)."""
import random
import time

import brute_force as bf
from datasets import clustered_points, random_query_rect, uniform_points
from quadtree import QuadTree

U, N, Q = 1024, 20_000, 200


def bench(name, pts):
    rng = random.Random(0)
    t0 = time.perf_counter()
    qt = QuadTree.from_points(pts, U, capacity=4)
    t_build = (time.perf_counter() - t0) * 1000
    rects = [random_query_rect(U, 0.01, rng) for _ in range(Q)]

    t0 = time.perf_counter()
    r_bf = [len(bf.range_query(pts, r)) for r in rects]
    t_bf = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    r_qt = [len(qt.range_query(r)) for r in rects]
    t_qt = (time.perf_counter() - t0) * 1000

    assert r_bf == r_qt, "¡resultados distintos!"
    print(f"{name:10s} build={t_build:7.1f} ms | {Q} consultas: "
          f"fuerza bruta={t_bf:8.1f} ms, quadtree={t_qt:8.1f} ms | "
          f"d={qt.depth()} nodos={qt.node_count()}")


if __name__ == "__main__":
    bench("uniforme", uniform_points(N, U, seed=1))
    bench("clusters", clustered_points(N, U, seed=1))
