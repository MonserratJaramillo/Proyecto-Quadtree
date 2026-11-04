import unittest

import brute_force as bf
from geometry import Point, Rect


class TestBruteForce(unittest.TestCase):
    def setUp(self):
        self.pts = [Point(1, 1), Point(2, 2), Point(5, 5), Point(9, 9), Point(5, 1)]

    def test_range_query(self):
        res = bf.range_query(self.pts, Rect(0, 0, 5, 5))
        self.assertEqual(set(res), {Point(1, 1), Point(2, 2), Point(5, 5), Point(5, 1)})

    def test_range_vacio(self):
        self.assertEqual(bf.range_query(self.pts, Rect(6, 6, 8, 8)), [])

    def test_count_y_density(self):
        r = Rect(0, 0, 4, 4)                       # área 16, 2 puntos
        self.assertEqual(bf.count_in_range(self.pts, r), 2)
        self.assertAlmostEqual(bf.density(self.pts, r), 2 / 16)

    def test_density_area_cero(self):
        with self.assertRaises(ValueError):
            bf.density(self.pts, Rect(1, 1, 1, 5))

    def test_radius(self):
        res = bf.radius_query(self.pts, Point(1, 1), 2 ** 0.5)
        self.assertEqual(set(res), {Point(1, 1), Point(2, 2)})
        with self.assertRaises(ValueError):
            bf.radius_query(self.pts, Point(0, 0), -1)

    def test_nearest(self):
        self.assertEqual(bf.nearest_neighbor(self.pts, Point(8, 8)), Point(9, 9))

    def test_nearest_excluyendo_el_mismo(self):
        p = self.pts[0]
        self.assertEqual(bf.nearest_neighbor(self.pts, p, exclude=p), Point(2, 2))

    def test_nearest_vacio(self):
        self.assertIsNone(bf.nearest_neighbor([], Point(0, 0)))


if __name__ == "__main__":
    unittest.main()
