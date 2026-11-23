"""S4: el recuento del oráculo reproduce J4:O11 de OD/AP (1).xlsx (conteos tecleados y fórmulas en caché)."""
import os
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from tsci3 import datos  # noqa: E402

OD = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "fuentes", "OD")
REGLAS = [("HeartDisease", "No", "Smoking", "No"), ("HeartDisease", "No", "Smoking", "Yes"),
          ("Smoking", "No", "HeartDisease", "No"), ("Smoking", "No", "HeartDisease", "Yes"),
          ("HeartDisease", "Yes", "Smoking", "No"), ("HeartDisease", "Yes", "Smoking", "Yes"),
          ("Smoking", "Yes", "HeartDisease", "No"), ("Smoking", "Yes", "HeartDisease", "Yes")]     # I4:I11


class AP(unittest.TestCase):
    def test_J4_O11(self):
        m = datos.leer_xlsx(os.path.join(OD, "AP (1).xlsx"), "Sheet1")
        enc = m[0][:5]
        filas = [dict(zip(enc, f[:5])) for f in m[1:51]]
        n = len(filas)
        self.assertEqual(n, m[1][10])                                                   # K2 = 50
        for r, (cx, vx, cy, vy) in enumerate(REGLAS, 3):
            nx = sum(1 for f in filas if f[cx] == vx)
            ny = sum(1 for f in filas if f[cy] == vy)
            nxy = sum(1 for f in filas if f[cx] == vx and f[cy] == vy)
            self.assertEqual((nx, ny, nxy), tuple(m[r][9:12]))                         # J:L tecleados
            self.assertAlmostEqual(nxy / n, m[r][12], places=12)                       # M = S
            self.assertAlmostEqual(nxy / nx, m[r][13], places=12)                      # N = C
            self.assertAlmostEqual(nxy * n / (nx * ny), m[r][14], places=12)           # O = L
        # mutante: NX·NY en el numerador del lift no da O4
        self.assertNotAlmostEqual(44 * 25 * 50 / 24, m[3][14], places=3)


if __name__ == "__main__":
    unittest.main()
