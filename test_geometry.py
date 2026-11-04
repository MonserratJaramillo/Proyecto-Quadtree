import unittest

from geometry import BoundingSquare, Point, Rect


class TestPoint(unittest.TestCase):
    def test_distancia(self):
        self.assertEqual(Point(0, 0).dist_sq(Point(3, 4)), 25)
        self.assertEqual(Point(0, 0).dist(Point(3, 4)), 5)


class TestRect(unittest.TestCase):
    def test_area_y_contiene(self):
        r = Rect(0, 0, 2, 3)
        self.assertEqual(r.area, 6)
        self.assertTrue(r.contains_point(Point(2, 3)))   # borde incluido
        self.assertFalse(r.contains_point(Point(2.1, 1)))

    def test_invalido(self):
        with self.assertRaises(ValueError):
            Rect(1, 0, 0, 1)


class TestBoundingSquare(unittest.TestCase):
    def setUp(self):
        self.sq = BoundingSquare(0, 0, 8)

    def test_cuadrantes_segun_documento(self):
        self.assertEqual(self.sq.quadrant_of(Point(5, 5)), "NE")
        self.assertEqual(self.sq.quadrant_of(Point(4, 5)), "NW")   # x == xmid
        self.assertEqual(self.sq.quadrant_of(Point(5, 4)), "SE")   # y == ymid
        self.assertEqual(self.sq.quadrant_of(Point(4, 4)), "SW")

    def test_hijos(self):
        self.assertEqual(self.sq.child("NE"), BoundingSquare(4, 4, 4))
        self.assertEqual(self.sq.child("SW"), BoundingSquare(0, 0, 4))
        self.assertEqual(self.sq.child("NW"), BoundingSquare(0, 4, 4))
        self.assertEqual(self.sq.child("SE"), BoundingSquare(4, 0, 4))

    def test_contiene_borde(self):
        self.assertTrue(self.sq.contains(Point(8, 8)))
        self.assertFalse(self.sq.contains(Point(8.01, 0)))

    def test_interseccion_e_inside(self):
        self.assertTrue(self.sq.intersects(Rect(7, 7, 20, 20)))
        self.assertFalse(self.sq.intersects(Rect(9, 9, 20, 20)))
        self.assertTrue(self.sq.inside(Rect(-1, -1, 9, 9)))
        self.assertFalse(self.sq.inside(Rect(1, 1, 9, 9)))

    def test_min_dist(self):
        self.assertEqual(self.sq.min_dist_sq(Point(4, 4)), 0)
        self.assertEqual(self.sq.min_dist_sq(Point(11, 12)), 9 + 16)

    def test_size_invalido(self):
        with self.assertRaises(ValueError):
            BoundingSquare(0, 0, 0)


if __name__ == "__main__":
    unittest.main()
