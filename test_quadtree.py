import random
import unittest

import brute_force as bf
from datasets import clustered_points, random_query_rect, uniform_points
from geometry import BoundingSquare, Point, Rect
from quadtree import QuadTree

U = 256


def key(points):
    return sorted((p.x, p.y) for p in points)


class TestConstruccion(unittest.TestCase):
    def test_insert_y_len(self):
        qt = QuadTree(U, capacity=1)
        self.assertTrue(qt.insert(Point(10, 10)))
        self.assertTrue(qt.insert(Point(200, 200)))
        self.assertEqual(len(qt), 2)
        self.assertTrue(qt.root.divided)

    def test_punto_fuera_se_rechaza(self):
        qt = QuadTree(U)
        self.assertFalse(qt.insert(Point(-1, 5)))
        self.assertFalse(qt.insert(Point(5, U + 1)))
        self.assertEqual(len(qt), 0)

    def test_puntos_en_los_bordes(self):
        qt = QuadTree.from_points([Point(0, 0), Point(U, U), Point(U, 0)], U)
        self.assertEqual(len(qt), 3)

    def test_duplicados_no_recursion_infinita(self):
        qt = QuadTree.from_points([Point(3, 3)] * 10, U, capacity=1)
        self.assertEqual(len(qt), 10)
        self.assertLessEqual(qt.depth(), qt.max_depth)

    def test_profundidad_maxima_log2U(self):
        self.assertEqual(QuadTree(256).max_depth, 8)

    def test_conserva_todos_los_puntos(self):
        pts = uniform_points(500, U, seed=1)
        qt = QuadTree.from_points(pts, U, capacity=2)
        stored = [p for leaf in qt.leaves() for p in leaf.points]
        self.assertEqual(key(stored), key(pts))
        self.assertEqual(sum(l.n_points for l in qt.leaves()), 500)

    def test_cota_de_nodos(self):                    # O((d+1) n)
        pts = uniform_points(1000, U, seed=2)
        qt = QuadTree.from_points(pts, U)
        self.assertLessEqual(qt.node_count(), 4 * (qt.depth() + 1) * len(pts) + 1)


class TestContraFuerzaBruta(unittest.TestCase):
    """El quadtree debe dar exactamente lo mismo que la fuerza bruta."""

    def _datasets(self):
        for n in (1, 10, 200, 1000):
            yield uniform_points(n, U, seed=n)
            yield clustered_points(n, U, seed=n)

    def test_range_query(self):
        rng = random.Random(7)
        for pts in self._datasets():
            for cap in (1, 4):
                qt = QuadTree.from_points(pts, U, capacity=cap)
                for frac in (0.01, 0.1, 0.5):
                    for _ in range(5):
                        r = random_query_rect(U, frac, rng)
                        self.assertEqual(key(qt.range_query(r)),
                                         key(bf.range_query(pts, r)))
                        self.assertEqual(qt.count_in_range(r),
                                         bf.count_in_range(pts, r))
                        self.assertAlmostEqual(qt.density(r), bf.density(pts, r))

    def test_radius_query(self):
        rng = random.Random(8)
        for pts in self._datasets():
            qt = QuadTree.from_points(pts, U)
            for _ in range(5):
                c = Point(rng.uniform(0, U), rng.uniform(0, U))
                r = rng.uniform(1, 60)
                self.assertEqual(key(qt.radius_query(c, r)),
                                 key(bf.radius_query(pts, c, r)))

    def test_nearest_neighbor(self):
        rng = random.Random(9)
        for pts in self._datasets():
            qt = QuadTree.from_points(pts, U)
            for _ in range(10):
                q = Point(rng.uniform(0, U), rng.uniform(0, U))
                a, b = qt.nearest_neighbor(q), bf.nearest_neighbor(pts, q)
                self.assertAlmostEqual(a.dist_sq(q), b.dist_sq(q))

    def test_nearest_excluyendo_el_mismo(self):
        pts = uniform_points(300, U, seed=3)
        qt = QuadTree.from_points(pts, U)
        for p in pts[:30]:
            a = qt.nearest_neighbor(p, exclude=p)
            b = bf.nearest_neighbor(pts, p, exclude=p)
            self.assertAlmostEqual(a.dist_sq(p), b.dist_sq(p))

    def test_arbol_vacio(self):
        qt = QuadTree(U)
        self.assertEqual(qt.range_query(Rect(0, 0, U, U)), [])
        self.assertIsNone(qt.nearest_neighbor(Point(1, 1)))


class TestVecinosDeCelda(unittest.TestCase):
    OFFSET = {"N": (0.5, 1.25), "S": (0.5, -0.25), "E": (1.25, 0.5), "W": (-0.25, 0.5)}

    def test_find_neighbor_coincide_con_busqueda_por_coordenadas(self):
        qt = QuadTree.from_points(clustered_points(300, U, seed=4), U)
        for leaf in qt.leaves():
            b = leaf.boundary
            for d, (ox, oy) in self.OFFSET.items():
                px, py = b.x + ox * b.size, b.y + oy * b.size
                nb = leaf.find_neighbor(d)
                if not qt.root.boundary.contains_xy(px, py):
                    self.assertIsNone(nb)
                else:
                    self.assertIsNotNone(nb)
                    self.assertTrue(nb.boundary.contains_xy(px, py))
                    self.assertGreaterEqual(nb.boundary.size, b.size)

    def test_raiz_sin_vecinos(self):
        qt = QuadTree(U)
        for d in "NSEW":
            self.assertIsNone(qt.root.find_neighbor(d))


def balanceado_por_pares(qt):
    """Verificación independiente O(L^2): hojas que se tocan (arista o vértice)."""
    leaves = [l.boundary for l in qt.leaves()]
    for i, a in enumerate(leaves):
        for b in leaves[i + 1:]:
            toca = (a.x <= b.x + b.size and b.x <= a.x + a.size
                    and a.y <= b.y + b.size and b.y <= a.y + a.size)
            if toca and max(a.size, b.size) > 2 * min(a.size, b.size):
                return False
    return True


class TestBalanceo(unittest.TestCase):
    def test_arbol_desbalanceado_se_detecta(self):
        # dos puntos pegados al centro fuerzan celdas finas junto a una hoja enorme
        qt = QuadTree.from_points([Point(127, 127), Point(127.5, 127.5)], U)
        self.assertFalse(balanceado_por_pares(qt))
        self.assertFalse(qt.is_balanced())

    def test_balance_logra_regla_2_a_1(self):
        for seed in range(5):
            for pts in (uniform_points(60, U, seed), clustered_points(100, U, seed=seed)):
                qt = QuadTree.from_points(pts, U)
                qt.balance()
                self.assertTrue(qt.is_balanced())
                self.assertTrue(balanceado_por_pares(qt))

    def test_balance_no_pierde_puntos_ni_cambia_consultas(self):
        pts = clustered_points(400, U, seed=11)
        qt = QuadTree.from_points(pts, U)
        qt.balance()
        self.assertEqual(len(qt), len(pts))
        r = Rect(10, 10, 120, 200)
        self.assertEqual(key(qt.range_query(r)), key(bf.range_query(pts, r)))

    def test_balance_idempotente(self):
        qt = QuadTree.from_points(clustered_points(200, U, seed=5), U)
        qt.balance()
        self.assertEqual(qt.balance(), 0)


if __name__ == "__main__":
    unittest.main()
