# =============================================================================
# ARBOLES DE DECISION EN R: ID3 de minima entropia por niveles, rpart y ctree
# =============================================================================
# Datos   : datos/<ARCHIVO>; clase <CLASE>; TODOS los demas atributos (R1).
# Parte 1 : ID3 programado en R base (mismo metodo que resolver.py, por niveles).
# Parte 2 : los dos arboles de R: rpart (Gini y entropia) y ctree (partykit).
# Parte 3 : comparacion (raiz, hojas, profundidad, clases que predice, exactitud).
# Ejecutar: Rscript codigo/script.R        (desde la carpeta del problema)
# Paquetes: rpart (viene con R), partykit
# =============================================================================

ARCHIVO <- "gastank.csv"
CLASE   <- "Type"
VACIO   <- "Sin especificar"

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
suppressPackageStartupMessages({ library(rpart); library(partykit) })
options(width = 200)

# ---- Datos: las celdas vacias de los atributos pasan a la categoria VACIO (T16)
crudo <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE,
                  stringsAsFactors = FALSE, na.strings = character(0))
atributos <- setdiff(names(crudo), CLASE)
for (a in atributos) {
  vacios <- trimws(crudo[[a]]) == ""
  if (any(vacios)) cat(sprintf("%s: %d celdas vacias -> '%s'\n", a, sum(vacios), VACIO))
  crudo[[a]][vacios] <- VACIO
}
cat(sprintf("Registros: %d   Clase: %s   Atributos: %s\n", nrow(crudo), CLASE,
            paste(atributos, collapse = ", ")))
cat("Valores distintos:", paste(sprintf("%s=%d", atributos,
    sapply(atributos, function(a) length(unique(crudo[[a]])))), collapse = ", "), "\n")

# ---- Parte 1: ID3 por niveles en R base -------------------------------------
entropia <- function(y) {
  p <- table(y) / length(y); p <- p[p > 0]
  0 - sum(p * log2(p))
}
evaluar <- function(d, a) {
  g <- split(d[[CLASE]], d[[a]], drop = TRUE)
  pesos <- sapply(g, length) / nrow(d)
  e <- sum(pesos * sapply(g, entropia))
  list(E = e, split = -sum(pesos * log2(pesos)), ramas = length(g))
}
filas_id3 <- list()
hojas_id3 <- list()
pendientes <- list(list(ruta = character(0), d = crudo, libres = atributos))
nivel <- 0
while (length(pendientes)) {
  nivel <- nivel + 1
  siguientes <- list()
  cat(sprintf("\n===== NIVEL %d =====\n", nivel))
  for (nd in pendientes) {
    h <- entropia(nd$d[[CLASE]])
    tab <- table(nd$d[[CLASE]])
    mayor <- sort(names(tab)[tab == max(tab)])[1]
    ruta_txt <- if (length(nd$ruta)) paste(nd$ruta, collapse = " y ") else "raiz"
    if (h == 0 || !length(nd$libres)) {
      hojas_id3[[length(hojas_id3) + 1]] <- data.frame(ruta = ruta_txt, clase = mayor,
        n = nrow(nd$d), aciertos = max(tab))
      next
    }
    ev <- lapply(nd$libres, function(a) evaluar(nd$d, a)); names(ev) <- nd$libres
    E <- sapply(ev, `[[`, "E"); gan <- h - E; gan[abs(gan) < 1e-12] <- 0
    cat(sprintf("Nodo [%s] n=%d H=%.4f\n", ruta_txt, nrow(nd$d), h))
    for (a in nd$libres) {
      cat(sprintf("   E(%s)=%.4f  ganancia=%.4f  ramas=%d\n", a, E[[a]], gan[[a]], ev[[a]]$ramas))
      filas_id3[[length(filas_id3) + 1]] <- data.frame(nivel = nivel, ruta = ruta_txt,
        atributo = a, E = E[[a]], ganancia = gan[[a]])
    }
    mejor <- nd$libres[which.min(round(E, 12))]
    if (max(gan) <= 0) {
      cat(sprintf("   -> hoja %s (ganancia 0)\n", mayor))
      hojas_id3[[length(hojas_id3) + 1]] <- data.frame(ruta = ruta_txt, clase = mayor,
        n = nrow(nd$d), aciertos = max(tab))
      next
    }
    cat(sprintf("   -> se divide por %s\n", mejor))
    for (v in sort(unique(nd$d[[mejor]]))) {
      siguientes[[length(siguientes) + 1]] <- list(
        ruta = c(nd$ruta, sprintf("%s = %s", mejor, v)),
        d = nd$d[nd$d[[mejor]] == v, , drop = FALSE],
        libres = setdiff(nd$libres, mejor))
    }
  }
  pendientes <- siguientes
}
id3 <- do.call(rbind, filas_id3)
hojas <- do.call(rbind, hojas_id3)
acc_id3 <- sum(hojas$aciertos) / nrow(crudo)
cat(sprintf("\nID3 en R: %d hojas, %d/%d aciertos = %.2f %%\n", nrow(hojas),
            sum(hojas$aciertos), nrow(crudo), 100 * acc_id3))
write.csv(id3, file.path(base, "id3_R.csv"), row.names = FALSE)

# ---- Parte 2: los dos arboles de R con TODOS los atributos (R1) -------------
df <- as.data.frame(lapply(crudo, factor))
names(df) <- make.names(names(crudo))
y <- make.names(CLASE)
# T19: un atributo nominal con mas de 30 niveles no se puede usar como factor en R:
#   rpart evaluaria 2^(k-1) - 1 particiones (con 163 niveles no termino en 600 s) y
#   ctree (partykit) no busca divisiones no ordenadas con 31 niveles o mas.
#   No se excluye (R1): se usa su codigo entero = posicion alfabetica del nivel.
LIMITE <- 30
muchos <- setdiff(names(df)[sapply(df, nlevels) > LIMITE], y)
for (a in muchos) {
  orig <- names(crudo)[make.names(names(crudo)) == a][1]
  cat(sprintf("Nota T19: %s tiene %d niveles; en rpart y ctree se usa su codigo entero (orden alfabetico), no se excluye (R1).\n",
              orig, nlevels(df[[a]])))
  write.csv(data.frame(codigo = seq_len(nlevels(df[[a]])), nivel = levels(df[[a]])),
            file.path(base, sprintf("codigos_%s.csv", a)), row.names = FALSE)
  df[[a]] <- as.integer(df[[a]])
}
formula <- as.formula(paste(y, "~ ."))
cat("\nFormula de R:", deparse(formula), "\n")

t_gini <- system.time(m_gini <- rpart(formula, data = df, method = "class"))
cat(sprintf("\nrpart (indice de Gini) - %.1f s\n", t_gini[["elapsed"]])); print(m_gini)
t_info <- system.time(m_info <- rpart(formula, data = df, method = "class",
                                      parms = list(split = "information")))
cat(sprintf("\nrpart (entropia, split = 'information') - %.1f s\n", t_info[["elapsed"]])); print(m_info)
t_ct <- system.time(m_ct <- ctree(formula, data = df))
cat(sprintf("\nctree (partykit, alpha = 0.05) - %.1f s\n", t_ct[["elapsed"]])); print(m_ct)

# ---- Parte 3: comparacion ----------------------------------------------------
resumen_rpart <- function(m, nombre, criterio) {
  fr <- m$frame
  prof <- max(floor(log2(as.numeric(rownames(fr)))))
  pred <- predict(m, df, type = "class")
  data.frame(Modelo = nombre, Criterio = criterio,
             Raiz = if (fr$var[1] == "<leaf>") "(sin division)" else as.character(fr$var[1]),
             Hojas = sum(fr$var == "<leaf>"), Profundidad = prof,
             Clases_que_predice = paste(sort(unique(as.character(pred))), collapse = "; "),
             Exactitud = mean(pred == df[[y]]))
}
raiz_ct <- function(m) {
  s <- split_node(node_party(m))
  if (is.null(s)) "(sin division)" else names(m$data)[varid_split(s)]
}
pred_ct <- predict(m_ct, df)
comp <- rbind(
  resumen_rpart(m_gini, "rpart", "indice de Gini + poda por cp"),
  resumen_rpart(m_info, "rpart (information)", "entropia + poda por cp"),
  data.frame(Modelo = "ctree", Criterio = "pruebas de independencia (p-valor)",
             Raiz = raiz_ct(m_ct), Hojas = length(nodeids(m_ct, terminal = TRUE)),
             Profundidad = depth(m_ct),
             Clases_que_predice = paste(sort(unique(as.character(pred_ct))), collapse = "; "),
             Exactitud = mean(pred_ct == df[[y]])))
comp$Raiz <- sapply(comp$Raiz, function(r) names(crudo)[make.names(names(crudo)) == r][1])
cat("\nComparacion de los arboles de R:\n"); print(comp, row.names = FALSE)
write.csv(comp, file.path(base, "comparacion_R.csv"), row.names = FALSE)
write.csv(data.frame(rpart = predict(m_gini, df, type = "class"),
                     rpart_information = predict(m_info, df, type = "class"),
                     ctree = pred_ct),
          file.path(base, "predicciones_R.csv"), row.names = FALSE)
