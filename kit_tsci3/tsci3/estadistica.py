"""Distribuciones para verificar salidas de R (solo biblioteca estándar).

Beta incompleta regularizada por fracción continua (Lentz) y gamma incompleta regularizada
(serie y fracción continua). Con ellas: valores p de t de Student, F de Fisher y χ².
"""
import math


def _betacf(a, b, x, it=500, eps=3e-16):
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, it + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1 + aa / c if abs(1 + aa / c) > 1e-300 else 1e-300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1 + aa / c if abs(1 + aa / c) > 1e-300 else 1e-300
        delta = d * c
        h *= delta
        if abs(delta - 1) < eps:
            break
    return h


def betainc(a, b, x):
    """I_x(a, b) regularizada."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1 - math.exp(lbt) * _betacf(b, a, 1 - x) / b


def gammainc_q(a, x):
    """Q(a, x) = 1 − P(a, x) regularizada."""
    if x <= 0:
        return 1.0
    if x < a + 1:
        s, term, n = 1 / a, 1 / a, a
        for _ in range(1000):
            n += 1
            term *= x / n
            s += term
            if abs(term) < abs(s) * 1e-16:
                break
        return 1 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b, c, d = x + 1 - a, 1 / 1e-300, 1 / (x + 1 - a)
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = b + an / c
        c = c if abs(c) > 1e-300 else 1e-300
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-16:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def p_t_dos_colas(t, gl):
    return betainc(gl / 2, 0.5, gl / (gl + t * t))


def p_f(f, gl1, gl2):
    """P(F > f)."""
    return betainc(gl2 / 2, gl1 / 2, gl2 / (gl2 + gl1 * f))


def p_chi2(x, gl):
    """P(χ² > x)."""
    return gammainc_q(gl / 2, x / 2)
