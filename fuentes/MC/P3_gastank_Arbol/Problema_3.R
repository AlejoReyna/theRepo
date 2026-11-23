# =============================================================================
# PROBLEMA 3 (U.T.3) - Arbol de decision de minima entropia para gastank
# =============================================================================
# 1. Construye "a mano" el arbol ID3 (en cada nodo elige el atributo que deja
#    la MINIMA entropia ponderada = maxima ganancia de informacion).
# 2. Obtiene los dos arboles de R: rpart (CART) y ctree (partykit, arbol de
#    inferencia condicional).
# 3. Compara los tres arboles: raiz, particiones, hojas, profundidad y
#    exactitud (re-sustitucion y validacion 70/30 con semilla = matricula).
#
# Uso:  Rscript Problema_3.R                   (usa gastank.csv junto al script)
#       Rscript Problema_3.R /ruta/gastank.csv
# Paquetes: rpart (incluido en R), partykit y rpart.plot
#   install.packages(c("partykit", "rpart.plot"))
# =============================================================================

invisible(Sys.setlocale("LC_ALL", "en_US.UTF-8"))  # acentos correctos en consola y graficas
suppressPackageStartupMessages({
  library(rpart)
  library(rpart.plot)
  library(partykit)
})

arg_file <- grep("^--file=", commandArgs(FALSE), value = TRUE)
aqui <- if (length(arg_file)) dirname(normalizePath(sub("^--file=", "", arg_file[1]))) else getwd()
args <- commandArgs(trailingOnly = TRUE)
ruta <- if (length(args)) args[1] else file.path(aqui, "gastank.csv")
if (!file.exists(ruta)) stop("No encuentro ", ruta)

sink(file.path(aqui, "reporte_P3.txt"), split = TRUE)
options(width = 110)
linea <- function(t = "") cat(t, "\n", sep = "")
titulo <- function(t) { linea(); linea(strrep("-", 78)); linea(t); linea(strrep("-", 78)) }

# -----------------------------------------------------------------------------
# 0. Carga y tratamiento minimo
# -----------------------------------------------------------------------------
crudo <- read.csv(ruta, stringsAsFactors = FALSE, check.names = FALSE,
                  na.strings = character(0), strip.white = TRUE)
titulo("0. DATOS")
linea(sprintf("Archivo: %s   filas: %d   columnas: %d", basename(ruta), nrow(crudo), ncol(crudo)))
linea(sprintf("Valores vacios por columna: %s",
              paste(names(crudo), colSums(crudo == ""), sep = "=", collapse = ", ")))

df <- data.frame(
  Modelo      = crudo[["Model Name"]],
  Tipo        = crudo[["Type"]],
  Combustible = crudo[["Fuel Type"]],
  Ventilacion = ifelse(crudo[["Vent Type"]] == "", "Sin especificar", crudo[["Vent Type"]]),
  stringsAsFactors = TRUE
)
linea("Tratamiento: 'Vent Type' vacio -> categoria 'Sin especificar' (151 filas; en las")
linea("bombas de calor electricas significa 'no ventila', por eso se conserva como categoria")
linea("y no se elimina ni se imputa). 'Gas,Propane' se conserva como categoria propia")
linea("(equipo apto para ambos combustibles).")
linea()
linea("Clase objetivo: Tipo (Type). Predictores: Combustible (Fuel Type) y Ventilacion (Vent Type).")
linea(sprintf("Model Name se EXCLUYE: es practicamente un identificador (%d valores distintos para %d filas).",
              nlevels(df$Modelo), nrow(df)))
print(table(Tipo = df$Tipo))
linea()
print(table(Ventilacion = df$Ventilacion, Tipo = df$Tipo))
linea()
print(table(Combustible = df$Combustible, Tipo = df$Tipo))

# -----------------------------------------------------------------------------
# 1. Funciones de entropia y ganancia
# -----------------------------------------------------------------------------
entropia <- function(y) {
  p <- prop.table(table(droplevels(as.factor(y))))
  p <- p[p > 0]
  abs(-sum(p * log2(p)))  # abs() evita imprimir -0.000 en nodos puros
}
medidas <- function(d, a, clase = "Tipo") {
  H <- entropia(d[[clase]])
  partes <- split(d[[clase]], d[[a]], drop = TRUE)
  E <- sum(sapply(partes, function(y) length(y) / nrow(d) * entropia(y)))
  SI <- entropia(d[[a]])
  c(H_padre = H, E_ponderada = E, ganancia = H - E, split_info = SI, razon_ganancia = (H - E) / SI)
}

titulo("1. NODO RAIZ: entropia ponderada de cada atributo (se busca la MINIMA)")
H0 <- entropia(df$Tipo)
p0 <- prop.table(table(df$Tipo))
linea(sprintf("H(Tipo) = -sum p*log2(p) = %s = %.4f bits",
              paste(sprintf("-(%.4f)log2(%.4f)", p0, p0), collapse = " "), H0))
raiz <- t(sapply(c("Ventilacion", "Combustible", "Modelo"), function(a) medidas(df, a)))
print(round(raiz, 4))
linea("Detalle de E(Ventilacion) = sum |Sv|/|S| * H(Sv):")
for (v in levels(df$Ventilacion)) {
  s <- df$Tipo[df$Ventilacion == v]
  linea(sprintf("  %-18s n=%3d  H=%.4f  peso=%.4f  aporte=%.4f", v, length(s), entropia(s),
                length(s) / nrow(df), length(s) / nrow(df) * entropia(s)))
}
linea("Modelo tendria la mayor ganancia (1.53) pero es el sesgo conocido de ID3 hacia")
linea("atributos con muchos valores: generaria 163 ramas, no generaliza (razon de ganancia 0.28).")
linea("Entre los atributos validos, Ventilacion deja la menor entropia (0.786 < 1.085) -> RAIZ.")

# -----------------------------------------------------------------------------
# 2. ID3 (minima entropia)
# -----------------------------------------------------------------------------
clases <- levels(df$Tipo)
id3 <- function(d, atributos, clase = "Tipo") {
  y <- factor(d[[clase]], levels = clases)
  tab <- table(y)
  nodo <- list(n = nrow(d), dist = tab, H = entropia(y), clase = names(which.max(tab)))
  if (nodo$H == 0 || length(atributos) == 0) return(nodo)
  g <- sapply(atributos, function(a) medidas(d, a, clase)[["ganancia"]])
  if (max(g) <= 1e-12) return(nodo)
  mejor <- atributos[which.max(g)]
  nodo$atributo <- mejor
  nodo$ganancias <- g
  nodo$hijos <- lapply(split(d, d[[mejor]], drop = TRUE),
                       function(s) id3(s, setdiff(atributos, mejor), clase))
  nodo
}
# Simplificacion: si todos los hijos son hojas de la MISMA clase, el corte no cambia
# ninguna prediccion y el nodo se vuelve hoja (poda trivial).
simplificar <- function(nodo) {
  if (is.null(nodo$hijos)) return(nodo)
  nodo$hijos <- lapply(nodo$hijos, simplificar)
  hojas <- all(sapply(nodo$hijos, function(h) is.null(h$hijos)))
  if (hojas && length(unique(sapply(nodo$hijos, `[[`, "clase"))) == 1) {
    nodo$podado <- sprintf("%s (ganancia %.4f) no cambia la clase", nodo$atributo,
                           max(nodo$ganancias))
    nodo$hijos <- NULL
    nodo$atributo <- NULL
  }
  nodo
}
predecir_id3 <- function(nodo, fila) {
  while (!is.null(nodo$hijos)) {
    v <- as.character(fila[[nodo$atributo]])
    if (!v %in% names(nodo$hijos)) break
    nodo <- nodo$hijos[[v]]
  }
  nodo$clase
}
imprimir_id3 <- function(nodo, sangria = "", rama = "RAIZ") {
  dist <- paste(sprintf("%s=%d", abreviar(names(nodo$dist)), nodo$dist)[nodo$dist > 0], collapse = " ")
  if (is.null(nodo$hijos)) {
    extra <- if (!is.null(nodo$podado)) paste0("  [poda: ", nodo$podado, "]") else ""
    linea(sprintf("%s%s -> HOJA: %s  (n=%d, aciertos=%d, H=%.3f) {%s}%s", sangria, rama, nodo$clase,
                  nodo$n, max(nodo$dist), nodo$H, dist, extra))
  } else {
    linea(sprintf("%s%s -> [%s]  n=%d  H=%.3f  ganancias: %s", sangria, rama, nodo$atributo, nodo$n,
                  nodo$H, paste(sprintf("%s=%.4f", names(nodo$ganancias), nodo$ganancias), collapse = ", ")))
    for (v in names(nodo$hijos)) imprimir_id3(nodo$hijos[[v]], paste0(sangria, "    "), paste0("= ", v))
  }
}
abreviar <- function(x) {
  map <- c("Electric Heat Pump" = "EHP", "Gas Storage" = "GS",
           "Gas Storage-type Instantaneous" = "GSI", "Gas Tankless" = "GT")
  ifelse(x %in% names(map), map[x], x)
}
contar <- function(nodo) {
  if (is.null(nodo$hijos)) return(c(hojas = 1, prof = 0))
  r <- sapply(nodo$hijos, contar)
  c(hojas = sum(r["hojas", ]), prof = 1 + max(r["prof", ]))
}

atributos <- c("Ventilacion", "Combustible")
arbol_id3_completo <- id3(df, atributos)
arbol_id3 <- simplificar(arbol_id3_completo)

titulo("2. ARBOL ID3 DE MINIMA ENTROPIA (todos los datos)")
linea("Abreviaturas: EHP=Electric Heat Pump, GS=Gas Storage, GSI=Gas Storage-type Instantaneous, GT=Gas Tankless")
linea()
imprimir_id3(arbol_id3)
pred_id3 <- factor(sapply(seq_len(nrow(df)), function(i) predecir_id3(arbol_id3, df[i, ])), levels = clases)
linea()
linea(sprintf("Hojas: %d (antes de la poda trivial: %d)   Profundidad: %d",
              contar(arbol_id3)["hojas"], contar(arbol_id3_completo)["hojas"], contar(arbol_id3)["prof"]))
linea(sprintf("Exactitud de re-sustitucion: %d/%d = %.2f%%", sum(pred_id3 == df$Tipo), nrow(df),
              100 * mean(pred_id3 == df$Tipo)))
print(table(Real = abreviar(as.character(df$Tipo)), Prediccion = abreviar(as.character(pred_id3))))

linea()
linea("Reglas del arbol ID3:")
reglas <- function(nodo, cond = character(0)) {
  if (is.null(nodo$hijos)) {
    linea(sprintf("  SI %s ENTONCES Tipo = %s   (%d/%d)", paste(cond, collapse = " Y "),
                  nodo$clase, max(nodo$dist), nodo$n))
  } else {
    for (v in names(nodo$hijos))
      reglas(nodo$hijos[[v]], c(cond, sprintf("%s = '%s'", nodo$atributo, v)))
  }
}
reglas(arbol_id3)

# Diagrama del arbol ID3 (Graphviz)
dot_id3 <- function(nodo) {
  L <- c('digraph ID3 {', '  rankdir=LR; nodesep=0.12; ranksep=0.9; pad=0.2;',
         '  node [fontname="Helvetica", fontsize=10]; edge [fontname="Helvetica", fontsize=9];',
         '  labelloc="t"; fontname="Helvetica"; fontsize=14;',
         paste0('  label=<<b>Árbol ID3 de mínima entropía - gastank (clase: Type)</b><br/>',
                '<font point-size="11">EHP=Electric Heat Pump · GS=Gas Storage · ',
                'GSI=Gas Storage-type Instantaneous · GT=Gas Tankless</font>>;'))
  k <- 0
  colores <- c(EHP = "#DDEFD9", GS = "#DCE8F7", GSI = "#F8E3D2", GT = "#EFE0F5")
  visitar <- function(nd) {
    k <<- k + 1
    id <- sprintf("n%d", k)
    if (is.null(nd$hijos)) {
      ab <- abreviar(nd$clase)
      L <<- c(L, sprintf('  %s [shape=box, style="rounded,filled", fillcolor="%s", label=<<b>%s</b><br/>n=%d · aciertos=%d<br/>H=%.3f>];',
                         id, colores[[ab]], ab, nd$n, max(nd$dist), nd$H))
    } else {
      L <<- c(L, sprintf('  %s [shape=ellipse, style=filled, fillcolor="#FFF4D6", label=<<b>%s</b><br/>n=%d · H=%.3f>];',
                         id, nd$atributo, nd$n, nd$H))
      for (v in names(nd$hijos)) {
        h <- visitar(nd$hijos[[v]])
        L <<- c(L, sprintf('  %s -> %s [label="%s"];', id, h, gsub(",", ", ", v)))
      }
    }
    id
  }
  visitar(nodo)
  c(L, '}')
}
writeLines(dot_id3(arbol_id3), file.path(aqui, "arbol_ID3.dot"))
if (nzchar(Sys.which("dot"))) {
  system2("dot", c("-Tpng", "-Gdpi=170", shQuote(file.path(aqui, "arbol_ID3.dot")), "-o",
                   shQuote(file.path(aqui, "arbol_ID3.png"))))
  system2("dot", c("-Tsvg", shQuote(file.path(aqui, "arbol_ID3.dot")), "-o",
                   shQuote(file.path(aqui, "arbol_ID3.svg"))))
}

# -----------------------------------------------------------------------------
# 3. Arboles de R
# -----------------------------------------------------------------------------
titulo("3a. ARBOL rpart (CART, criterio Gini, parametros por defecto: cp=0.01, minsplit=20)")
set.seed(1851265)
m_rpart <- rpart(Tipo ~ Ventilacion + Combustible, data = df, method = "class")
print(m_rpart)
linea()
printcp(m_rpart)
linea()
linea("Importancia de variables (rpart):")
print(round(m_rpart$variable.importance, 2))
pred_rpart <- predict(m_rpart, df, type = "class")
linea(sprintf("Exactitud de re-sustitucion rpart: %.2f%%", 100 * mean(pred_rpart == df$Tipo)))
print(table(Real = abreviar(as.character(df$Tipo)), Prediccion = abreviar(as.character(pred_rpart))))

titulo("3a'. rpart con criterio de ENTROPIA (split = 'information') - referencia")
m_rpart_info <- rpart(Tipo ~ Ventilacion + Combustible, data = df, method = "class",
                      parms = list(split = "information"))
print(m_rpart_info)
pred_rpart_info <- predict(m_rpart_info, df, type = "class")
linea(sprintf("Exactitud de re-sustitucion rpart-information: %.2f%%", 100 * mean(pred_rpart_info == df$Tipo)))

titulo("3b. ARBOL ctree (partykit, inferencia condicional, alpha = 0.05)")
m_ctree <- ctree(Tipo ~ Ventilacion + Combustible, data = df)
print(m_ctree)
pred_ctree <- predict(m_ctree, df)
linea(sprintf("Exactitud de re-sustitucion ctree: %.2f%%", 100 * mean(pred_ctree == df$Tipo)))
print(table(Real = abreviar(as.character(df$Tipo)), Prediccion = abreviar(as.character(pred_ctree))))

# Graficas (para dibujar se usan las clases abreviadas; el arbol es identico)
colores_clase <- c("#DDEFD9", "#DCE8F7", "#F8E3D2", "#EFE0F5")
df_graf <- df
levels(df_graf$Tipo) <- abreviar(levels(df_graf$Tipo))
png(file.path(aqui, "arbol_rpart.png"), width = 1800, height = 1050, res = 220)
rpart.plot(rpart(Tipo ~ Ventilacion + Combustible, data = df_graf, method = "class"),
           type = 4, extra = 104, under = TRUE, faclen = 0, varlen = 0, cex = 0.85,
           box.palette = as.list(colores_clase[c(1, 2, 4, 3)]), legend.x = NA,  # mismos colores que ID3
           main = "\u00c1rbol rpart (CART, Gini) - gastank")
mtext("EHP=Electric Heat Pump  GS=Gas Storage  GSI=Gas Storage-type Instantaneous  GT=Gas Tankless",
      side = 1, line = 3, cex = 0.7)
invisible(dev.off())
png(file.path(aqui, "arbol_ctree.png"), width = 2000, height = 1250, res = 200)
m_ctree_graf <- ctree(Tipo ~ Ventilacion + Combustible, data = df_graf)
plot(m_ctree_graf, main = "\u00c1rbol ctree (inferencia condicional) - gastank",
     gp = gpar(fontsize = 10),
     tp_args = list(beside = FALSE, fill = rev(colores_clase), id = TRUE))
invisible(dev.off())

# -----------------------------------------------------------------------------
# 4. Comparacion
# -----------------------------------------------------------------------------
titulo("4. COMPARACION DE LOS ARBOLES")
hojas_rpart <- sum(m_rpart$frame$var == "<leaf>")
prof_rpart <- max(rpart:::tree.depth(as.numeric(rownames(m_rpart$frame))))
hojas_ctree <- width(m_ctree)
prof_ctree <- depth(m_ctree)
raiz_rpart <- as.character(m_rpart$frame$var[1])
raiz_ctree <- names(data_party(m_ctree))[split_node(node_party(m_ctree))$varid]

# validacion 70/30 (misma particion para los tres)
set.seed(1851265)
idx <- sample(nrow(df), round(0.7 * nrow(df)))
entr <- df[idx, ]
prue <- df[-idx, ]
id3_e <- simplificar(id3(entr, atributos))
acc_id3 <- mean(sapply(seq_len(nrow(prue)), function(i) predecir_id3(id3_e, prue[i, ])) == prue$Tipo)
acc_rpart <- mean(predict(rpart(Tipo ~ Ventilacion + Combustible, data = entr, method = "class"),
                          prue, type = "class") == prue$Tipo)
acc_ctree <- mean(predict(ctree(Tipo ~ Ventilacion + Combustible, data = entr), prue) == prue$Tipo)

comp <- data.frame(
  Arbol = c("ID3 (minima entropia, a mano)", "rpart (CART-Gini)", "ctree (partykit)"),
  Criterio = c("Ganancia de informacion (entropia)", "Indice de Gini + poda por cp",
               "Pruebas de independencia (p-valor)"),
  Tipo_de_corte = c("Multirrama (un hijo por valor)", "Binario (agrupa categorias)",
                    "Binario (agrupa categorias)"),
  Raiz = c(arbol_id3$atributo, raiz_rpart, raiz_ctree),
  Hojas = c(contar(arbol_id3)["hojas"], hojas_rpart, hojas_ctree),
  Profundidad = c(contar(arbol_id3)["prof"], prof_rpart, prof_ctree),
  Exactitud_resustitucion = round(100 * c(mean(pred_id3 == df$Tipo), mean(pred_rpart == df$Tipo),
                                          mean(pred_ctree == df$Tipo)), 2),
  Exactitud_prueba_30 = round(100 * c(acc_id3, acc_rpart, acc_ctree), 2),
  check.names = FALSE
)
print(comp, row.names = FALSE, right = FALSE)
write.csv(comp, file.path(aqui, "comparacion_arboles.csv"), row.names = FALSE)
linea()
linea(sprintf("Particion de validacion: %d filas de entrenamiento / %d de prueba (semilla 1851265).",
              nrow(entr), nrow(prue)))

# Coincidencia de predicciones entre arboles
linea()
linea("Coincidencia de predicciones sobre las 737 filas:")
linea(sprintf("  ID3 vs rpart: %.2f%%   ID3 vs ctree: %.2f%%   rpart vs ctree: %.2f%%",
              100 * mean(pred_id3 == pred_rpart), 100 * mean(pred_id3 == pred_ctree),
              100 * mean(pred_rpart == pred_ctree)))
sink()
