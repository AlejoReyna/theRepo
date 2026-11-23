---
name: tsci3-regresion-logistica
description: Regresión logística binaria y multinomial en TSCI3 (OD/AM R.pdf p.37-41) - sigmoide, glm(family = binomial) con precio > mediana, summary, car::Anova y vif con su lectura (1; 1 a 5; más de 5 o 10), multinom con percentiles 0.33/0.66 y cut(right = FALSE), predict(type = "probs") con datos nuevos, con la discrepancia T25 (wts[1:3] no son los interceptos) - con oráculo de Newton independiente de R, Excel con la probabilidad sustituida a mano y script R. Úsala cuando pidan "regresión logística", "glm binomial", "multinomial", "multinom", "VIF", "sigmoide" o "probabilidad de categoría" (TSCI3 AF4 Regresión logística binaria y multinomial).
---

# Regresión logística binaria y multinomial

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-regresion-logistica/scripts`.

## Criterio de rúbrica
AF4 Regresión logística binaria (6) y multinomial (6): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- p.37: la sigmoide convierte η = β0 + Σβjxj en la probabilidad p = 1/(1 + e^(−η)). p.38: la binaria predice si un evento ocurre (1/0); la multinomial, una de varias categorías.
- p.39: VIF de 1 = sin colinealidad; de 1 a 5 = moderada; más de 5 o 10 = preocupante.
- p.40: `precio_alto <- as.integer(precio > mediana)` (mayor estricto; el KNN de p.48 usa ≥); `glm(precio_alto ~ recamaras + baños + m2_construcción + m2_terreno, family = binomial)`, `summary`, `Anova` y `vif`.
- p.41: `quantile(precio, 0.33)` y `0.66` (tipo 7); `cut(..., right = FALSE)` con intervalos [a, b); `multinom`; `predict(new_data, type = "probs")` con (3, 2, 120, 200).
- **T25:** p.41 hace `intercepts <- model_multinom$wts[1:nlevels]`, pero esos tres pesos valen 0 (son de la clase base). Los interceptos están en `coef(model_multinom)[, 1]`; la entrega usa esos.
- Para p.40 no hay datos nuevos en las láminas. La skill usa los de p.41 para la sustitución a mano y lo declara.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV en `$I/datos/`; `parametros.json`: `{"archivo", "y", "predictores", "nuevos"}` (ejemplo: `$T/incisos/LOG-br`).
2. R: `$SC/script_logistica.R` → `$I/codigo/script.R`; `cd $I && Rscript codigo/script.R > salida_R.txt 2>&1`.
3. Verificación: `python3 $SC/verificar_logistica.py $I`. Debe dar ✅ en todo y escribe `traza.json`.
4. Excel: `$T/.venv/bin/python $SC/excel_logistica.py $I` y luego `recalcular_excel.py`.

## Verificación
1. Binaria: Newton propio hasta 1e−14. β, errores estándar y devianza deben dar lo mismo que glm. La probabilidad nueva se calcula a mano en la sigmoide y debe igualar `predict`.
2. Anova tipo II: se reajusta sin cada variable y LR = ΔD, con p de χ²(1). VIF se calcula desde Var(β) como `car::vif`.
3. Multinomial: el oráculo alcanza el máximo de la log-verosimilitud; nnet queda a menos de 1e−4. Las probabilidades suman 1 y coinciden con `predict` a 1e−4. Los conteos de `cut` y los percentiles deben coincidir con R.
4. Mutante: usar ≥ o `right = TRUE` cambia los conteos y se detecta.
5. Excel: mediana, PERCENTILE.INC y COUNTIFS con [a, b). La sigmoide y el softmax van en fórmula y la suma da 1.

## Casos de referencia comprobados
- **BR (2).csv** (n = 1000):
  - Binaria:
    - Mediana 443 750, con 500 altos.
    - β = (−2.9723, −0.28954, 0.16544, 0.0060438, −5.87e−6).
    - Con (3, 2, 120, 200), η = −2.78598 y p = 0.058087.
    - Anova: m2_construcción LR 125.76; recamaras 6.50 (p = 0.0108); baños y m2_terreno no significativas.
    - VIF de 1.01 a 2.11: colinealidad moderada.
  - Multinomial:
    - P33 = 355 000 y P66 = 536 954; conteos 327/333/340. Con `right = TRUE` serían 335/325/340, porque 8 precios valen exactamente 355 000.
    - Probabilidades para (3, 2, 120, 200): bajo 0.7075, medio 0.2778, alto 0.0147.
  - Verificación 10/10; Excel 17/17.
