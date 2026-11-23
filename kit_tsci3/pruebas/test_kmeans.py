"""S2: el oráculo reproduce las cifras en caché de los Excel de k-means del profesor."""
import os
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from tsci3 import datos  # noqa: E402
from tsci3.oraculos import kmeans  # noqa: E402

OD = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "fuentes", "OD")


class Mochila(unittest.TestCase):
    def test_primera_iteracion_igual_al_cache(self):
        m = datos.leer_xlsx(os.path.join(OD, "mochila_.xlsx"))
        filas = [f[1:4] for f in m[9:] if f[0] is not None]
        it = kmeans.replica_excel(filas)
        for got, cache in zip(it["C0_nuevo"] + it["C1_nuevo"], m[5][9:12] + m[6][9:12]):   # J6:L7
            self.assertAlmostEqual(got, cache, places=12)
        self.assertAlmostEqual(it["suma_dmin"], m[7][9], places=6)                          # J8
        self.assertEqual((it["n0"], it["n1"]), (m[7][10], m[7][11]))                        # K8, L8


class Dolly(unittest.TestCase):
    def setUp(self):
        self.m = datos.leer_xlsx(os.path.join(OD, "DOLLY LIVES.xlsx"), "Sheet1")
        self.filas = [f[1:13] for f in self.m[7:56]]                                         # B8:M56

    def test_replica_con_error_T1(self):
        it = kmeans.replica_excel(self.filas, fija_columna=2, fila_fija=0)   # Danceability fija en la fila 8
        self.assertAlmostEqual(it["suma_dmin"], self.m[56][28], places=9)    # AC57
        self.assertEqual((it["n0"], it["n1"]), (self.m[56][29], self.m[56][30]))  # AD57, AE57
        for got, cache in zip(it["C0_nuevo"] + it["C1_nuevo"], self.m[1][32:44] + self.m[2][32:44]):  # AG2:AR3
            self.assertAlmostEqual(got, cache, places=12)

    def test_sin_error_cambia_la_suma(self):
        it = kmeans.replica_excel(self.filas)
        self.assertEqual((it["n0"], it["n1"]), (46, 3))
        self.assertNotAlmostEqual(it["suma_dmin"], self.m[56][28], places=3)



class DollyMedoides(unittest.TestCase):
    def test_replica_sheet2_con_error_T1(self):
        from tsci3.oraculos import kmedoides
        m = datos.leer_xlsx(os.path.join(OD, "DOLLY LIVES.xlsx"), "Sheet2")
        filas = [f[1:13] for f in m[7:56]]
        r = kmedoides.replica_excel(filas, fija_columna=2, fila_fija=0)
        self.assertAlmostEqual(r["min_dist_C0"], m[56][31], places=9)          # AF57
        self.assertAlmostEqual(r["min_dist_C1"], m[56][32], places=9)          # AG57
        for got, tecleado in zip(r["M0"] + r["M1"], m[3][32:44] + m[4][32:44]):  # AG4:AR5 (tecleados)
            self.assertAlmostEqual(got, tecleado, places=12)


if __name__ == "__main__":
    unittest.main()
