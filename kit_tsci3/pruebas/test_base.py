"""Paso 3 del plan: kit base contra las cifras en caché de OD/mochila_.xlsx."""
import os
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from tsci3 import datos, numeros  # noqa: E402

FUENTES = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "fuentes")
MOCHILA = os.path.join(FUENTES, "OD", "mochila_.xlsx")


class Mochila(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = datos.leer_xlsx(MOCHILA)
        cls.filas = [f for f in cls.m[9:] if f[0] is not None]  # datos desde la fila 10

    def test_registros(self):
        self.assertEqual(len(self.filas), 100000)
        self.assertEqual(self.filas[0][:4], [1, 2.7, 7.43, 29])

    def test_m_y_fila_1(self):
        cols = [[f[c] for f in self.filas] for c in (1, 2, 3)]
        ms, normal1 = [], []
        for v in cols:
            y, m, b = numeros.minmax(v)
            ms.append(m)
            normal1.append(y[0])
        for got, cache in zip(ms, (0.034483, 0.101010, 0.011111)):
            self.assertAlmostEqual(got, cache, places=6)
        for got, cache in zip(normal1, (0.058621, 0.740404, 0.211111)):
            self.assertAlmostEqual(got, cache, places=6)
        # y coincide con el valor en caché de la celda (B4:D4 y E10:G10)
        for j, c in enumerate((1, 2, 3)):
            self.assertAlmostEqual(ms[j], self.m[3][c], places=12)
            self.assertAlmostEqual(normal1[j], self.m[9][4 + j], places=12)


class Basicas(unittest.TestCase):
    def test_entropia(self):
        self.assertAlmostEqual(numeros.entropia([412, 210, 68, 47]), 1.5556, places=4)
        self.assertEqual(numeros.entropia([5, 0]), 0.0)

    def test_zscore_como_scale(self):
        z, media, sd = numeros.zscore([1, 2, 3, 4])
        self.assertAlmostEqual(sd, 1.2909944487358056)
        self.assertAlmostEqual(z[0], -1.161895003862225)

    def test_constante(self):
        with self.assertRaises(ValueError):
            numeros.minmax([3, 3, 3])


if __name__ == "__main__":
    unittest.main()
