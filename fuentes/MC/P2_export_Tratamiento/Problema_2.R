# =============================================================================
# PROBLEMA 2 (U.T.1) - Tratamiento de datos del registro "export" (CDC BRFSS)
# =============================================================================
# Registro: Nutrition, Physical Activity and Obesity - Behavioral Risk Factor
# Surveillance System (CDC), 2011-2025, 118,580 filas x 33 columnas.
#
# OBJETIVO DE MINERIA (clasificacion supervisada):
#   Predecir el NIVEL DE OBESIDAD ADULTA de un estado en un ano
#   (Baja < 30 %, Media 30-35 %, Alta >= 35 %; cortes de los mapas de
#   prevalencia del CDC) a partir de sus indicadores de ACTIVIDAD FISICA.
#   Objetivo secundario (descriptivo): perfil socioeconomico de la obesidad
#   (ingreso y escolaridad).
#
# El tratamiento usa SUBSETTINGS VARIADOS de R base:
#   por columnas (nombre, indice negativo, patron grepl, constantes/duplicadas),
#   por filas (condicion logica, subset(), %in%, which(), is.na, calidad),
#   por grupo (split), ordenamiento/top-n (order/head) y muestreo aleatorio.
#
# Uso:  Rscript Problema_2.R /ruta/export.csv
#       (sin argumento busca export.csv junto al script y luego en ~/Downloads)
# Solo R base + rpart (incluido en R).
# =============================================================================

invisible(Sys.setlocale("LC_ALL", "en_US.UTF-8"))
suppressPackageStartupMessages(library(rpart))

arg_file <- grep("^--file=", commandArgs(FALSE), value = TRUE)
aqui <- if (length(arg_file)) dirname(normalizePath(sub("^--file=", "", arg_file[1]))) else getwd()
args <- commandArgs(trailingOnly = TRUE)
candidatas <- c(args, file.path(aqui, "export.csv"), path.expand("~/Downloads/export.csv"))
ruta <- candidatas[file.exists(candidatas)][1]
if (is.na(ruta)) stop("No encuentro export.csv. Uso: Rscript Problema_2.R /ruta/export.csv")
salidas <- file.path(aqui, "salidas")
dir.create(salidas, showWarnings = FALSE)

sink(file.path(aqui, "reporte_P2.txt"), split = TRUE)
options(width = 120, scipen = 6)
linea <- function(...) cat(..., "\n", sep = "")
titulo <- function(t) { linea(); linea(strrep("=", 90)); linea(t); linea(strrep("=", 90)) }

bitacora <- data.frame(paso = character(0), operacion = character(0), subsetting = character(0),
                       filas = integer(0), columnas = integer(0), stringsAsFactors = FALSE)
registrar <- function(paso, operacion, subsetting, d) {
  bitacora[nrow(bitacora) + 1, ] <<- list(paso, operacion, subsetting, nrow(d), ncol(d))
  linea(sprintf("  -> [%s] %s: %s filas x %d columnas", paso, operacion,
                format(nrow(d), big.mark = ","), ncol(d)))
}

# -----------------------------------------------------------------------------
# 1. CARGA Y PERFILADO
# -----------------------------------------------------------------------------
titulo("1. CARGA Y PERFILADO DEL REGISTRO")
crudo <- read.csv(ruta, check.names = FALSE, na.strings = c("", "NA"), stringsAsFactors = FALSE)
registrar("P0", "Carga del archivo original", "-", crudo)
espacios <- names(crudo)[names(crudo) != trimws(names(crudo))]
names(crudo) <- trimws(names(crudo))

perfil <- data.frame(
  columna = names(crudo),
  tipo = sapply(crudo, function(x) class(x)[1]),
  n_distintos = sapply(crudo, function(x) length(unique(na.omit(x)))),
  n_faltantes = colSums(is.na(crudo)),
  pct_faltantes = round(100 * colMeans(is.na(crudo)), 1),
  ejemplo = sapply(crudo, function(x) substr(as.character(na.omit(x)[1]), 1, 40)),
  row.names = NULL
)
print(perfil, right = FALSE)
write.csv(perfil, file.path(salidas, "perfil_columnas.csv"), row.names = FALSE)

linea()
linea("Hallazgos del perfilado:")
linea(sprintf("  * %s filas; %d estados/territorios; anos %d-%d; %d preguntas (QuestionID).",
              format(nrow(crudo), big.mark = ","), length(unique(crudo$LocationAbbr)),
              min(crudo$YearStart), max(crudo$YearStart), length(unique(crudo$QuestionID))))
linea("  * Registro en formato LARGO: una fila = estado x ano x pregunta x estrato.")
linea(sprintf("  * Data_Value faltante en %s filas (%.1f%%): pie de nota 'sample size is insufficient'.",
              format(sum(is.na(crudo$Data_Value)), big.mark = ","), 100 * mean(is.na(crudo$Data_Value))))
linea("  * Sample_Size viene como texto con comas ('1,367') -> requiere conversion.")
linea(sprintf("  * Nombres con espacios sobrantes corregidos con trimws(): '%s'.", paste(espacios, collapse = "', '")))
linea("  * GeoLocation viene como texto '(lat, lon)' -> se separa en dos numericas.")
linea("  * Age(years)/Education/Sex/Income/Race/Total son la MISMA informacion que")
linea("    Stratification1, repartida en columnas casi vacias (formato disperso).")

linea()
linea("Diccionario de preguntas (QuestionID) y anos disponibles:")
preg <- unique(crudo[, c("QuestionID", "Class", "Question")])
preg <- preg[order(preg$QuestionID), ]
for (i in seq_len(nrow(preg))) {
  anos <- sort(unique(crudo$YearStart[crudo$QuestionID == preg$QuestionID[i]]))
  linea(sprintf("  %s [%s] %s", preg$QuestionID[i], preg$Class[i], substr(preg$Question[i], 1, 95)))
  linea(sprintf("       anos: %s", paste(anos, collapse = " ")))
}

# -----------------------------------------------------------------------------
# 2. SUBSETTING POR COLUMNAS (reduccion de atributos)
# -----------------------------------------------------------------------------
titulo("2. SUBSETTING POR COLUMNAS")
# 2a. columnas constantes (un solo valor no faltante) -> sin informacion
constantes <- names(crudo)[sapply(crudo, function(x) length(unique(na.omit(x))) <= 1)]
linea("2a. Constantes (un solo valor): ", paste(constantes, collapse = ", "))
# 2b. columnas duplicadas de otra columna
iguales <- function(x, y) isTRUE(all.equal(as.character(x), as.character(y)))
duplicadas <- c(if (iguales(crudo$YearEnd, crudo$YearStart)) "YearEnd",
                if (iguales(crudo$Data_Value_Alt, crudo$Data_Value)) "Data_Value_Alt",
                if (iguales(crudo$Topic, sub(" - Behavior$", "", crudo$Topic)) ||
                    length(unique(paste(crudo$Class, crudo$Topic))) == length(unique(crudo$Class))) "Topic")
linea("2b. Duplicadas de otra columna: ", paste(duplicadas, collapse = ", "),
      "  (YearEnd==YearStart, Data_Value_Alt==Data_Value, Topic 1:1 con Class)")
# 2c. estratos dispersos: se reconstruyen desde Stratification1 -> se eliminan (subsetting por NOMBRE)
dispersas <- c("Total", "Age(years)", "Education", "Sex", "Income", "Race/Ethnicity")
linea("2c. Estratos dispersos (redundantes con Stratification1): ", paste(dispersas, collapse = ", "))
# 2d. codigos que repiten a su descripcion (subsetting por PATRON)
codigos <- grep("ID$|Id1$|ID1$", names(crudo), value = TRUE)
codigos <- setdiff(codigos, c("QuestionID", "LocationID"))
linea("2d. Codigos equivalentes a su texto (grepl 'ID$|Id1$|ID1$'): ", paste(codigos, collapse = ", "))
fuera <- unique(c(constantes, duplicadas, dispersas, codigos, "Question", "LocationID"))
# subsetting por INDICE NEGATIVO
d <- crudo[, -which(names(crudo) %in% fuera)]
registrar("P1", "Eliminar columnas constantes, duplicadas, dispersas y codigos", "d[, -which(names %in% fuera)]", d)
linea("Columnas conservadas: ", paste(names(d), collapse = ", "))

# -----------------------------------------------------------------------------
# 3. LIMPIEZA Y TRANSFORMACION DE TIPOS
# -----------------------------------------------------------------------------
titulo("3. LIMPIEZA DE TIPOS")
d$Sample_Size <- as.numeric(gsub(",", "", d$Sample_Size))
coord <- regmatches(d$GeoLocation, regexec("\\(\\s*([-0-9.]+),\\s*([-0-9.]+)\\)", d$GeoLocation))
d$Latitud <- as.numeric(sapply(coord, function(x) if (length(x) == 3) x[2] else NA))
d$Longitud <- as.numeric(sapply(coord, function(x) if (length(x) == 3) x[3] else NA))
d$GeoLocation <- NULL
d$Ancho_IC <- d$High_Confidence_Limit - d$Low_Confidence_Limit
names(d)[names(d) == "YearStart"] <- "Anio"
linea("Sample_Size: texto con comas -> numerico. GeoLocation -> Latitud, Longitud.")
linea("Nueva variable derivada: Ancho_IC = High_Confidence_Limit - Low_Confidence_Limit (precision).")
linea("YearStart -> Anio.")
print(summary(d[, c("Data_Value", "Sample_Size", "Ancho_IC", "Latitud", "Longitud")]))
registrar("P2", "Conversion de tipos y variables derivadas", "d$col <- ...", d)

# -----------------------------------------------------------------------------
# 4. SUBSETTING POR FILAS
# -----------------------------------------------------------------------------
titulo("4. SUBSETTING POR FILAS")
# 4a. valores faltantes del objetivo/medida: no se imputan (son supresiones del CDC)
linea("4a. Filas sin Data_Value por pie de nota: ",
      paste(names(table(crudo$Data_Value_Footnote_Symbol)), table(crudo$Data_Value_Footnote_Symbol),
            sep = " -> ", collapse = "; "))
d <- subset(d, !is.na(Data_Value))
d$Data_Value_Footnote_Symbol <- NULL
d$Data_Value_Footnote <- NULL
registrar("P3", "Quitar filas sin valor (suprimidas por muestra insuficiente)", "subset(d, !is.na(Data_Value))", d)

# 4b. unidad de analisis = 50 estados + DC (se excluye el agregado nacional y territorios)
excluir <- c("US", "GU", "PR", "VI")
linea("4b. Se excluyen: US (agregado nacional, duplicaria la informacion de los estados) y")
linea("    GU, PR, VI (territorios con muchos faltantes y contexto distinto).")
d <- d[!(d$LocationAbbr %in% excluir), ]
registrar("P4", "Solo 50 estados + DC", "d[!(LocationAbbr %in% excluir), ]", d)

# 4c. filtro de calidad: estimaciones muy imprecisas (IC > 20 puntos) se descartan
umbral_ic <- 20
imprecisas <- which(d$Ancho_IC > umbral_ic)
linea(sprintf("4c. Filtro de calidad: %d filas con Ancho_IC > %d puntos (p90 del registro = %.1f).",
              length(imprecisas), umbral_ic, quantile(crudo$High_Confidence_Limit -
                                                         crudo$Low_Confidence_Limit, 0.9, na.rm = TRUE)))
d <- d[-imprecisas, ]
registrar("P5", "Quitar estimaciones imprecisas (IC > 20)", "d[-which(Ancho_IC > 20), ]", d)
write.csv(d, file.path(salidas, "export_limpio_largo.csv"), row.names = FALSE)

# -----------------------------------------------------------------------------
# 5. SUBCONJUNTOS PARA EL OBJETIVO PRINCIPAL -> VISTA MINABLE
# -----------------------------------------------------------------------------
titulo("5. VISTA MINABLE (estado x ano) PARA CLASIFICAR EL NIVEL DE OBESIDAD")
# 5a. solo el estrato Total (nivel estatal)
tot <- d[d$StratificationCategory1 == "Total", ]
registrar("P6", "Estrato 'Total' (nivel estatal)", "d[StratificationCategory1 == 'Total', ]", tot)
# 5b. solo las preguntas del objetivo (patron sobre la clase)
tot <- tot[grepl("Obesity|Physical Activity", tot$Class) & tot$QuestionID != "Q037", ]
registrar("P7", "Preguntas de obesidad (Q036) y actividad fisica (Q043-Q047)",
          "grepl('Obesity|Physical Activity', Class) & QuestionID != 'Q037'", tot)
linea("    Q037 (sobrepeso) se excluye: es otro resultado de peso, no un predictor (fuga de informacion).")
# 5c. anos en que existen TODAS las preguntas de actividad fisica
anos_pa <- Reduce(intersect, split(tot$Anio, tot$QuestionID))
linea("5c. Anos comunes a Q036 y Q043-Q047 (intersect de split por pregunta): ", paste(sort(anos_pa), collapse = ", "))
tot <- tot[tot$Anio %in% anos_pa, ]
registrar("P8", "Anos con todas las preguntas", "tot[Anio %in% anos_pa, ]", tot)

# 5d. pivoteo largo -> ancho
nombres_q <- c(Q036 = "obesidad", Q043 = "aerobica_150", Q044 = "aerobica150_y_fuerza",
               Q045 = "aerobica_300", Q046 = "fuerza_2dias", Q047 = "inactividad")
ancho <- reshape(tot[, c("LocationAbbr", "LocationDesc", "Anio", "QuestionID", "Data_Value")],
                 idvar = c("LocationAbbr", "LocationDesc", "Anio"), timevar = "QuestionID",
                 direction = "wide")
names(ancho) <- sub("^Data_Value\\.", "", names(ancho))
ancho <- ancho[, c("LocationAbbr", "LocationDesc", "Anio", names(nombres_q))]
names(ancho)[4:9] <- nombres_q
ancho <- ancho[order(ancho$LocationAbbr, ancho$Anio), ]
rownames(ancho) <- NULL
registrar("P9", "Pivoteo largo -> ancho (reshape)", "reshape(direction = 'wide')", ancho)

# 5e. faltantes en la vista: estado-ano sin encuesta -> no se imputa la clase
esperadas <- expand.grid(LocationAbbr = sort(unique(tot$LocationAbbr)), Anio = sort(anos_pa),
                         stringsAsFactors = FALSE)
ausentes <- esperadas[!paste(esperadas$LocationAbbr, esperadas$Anio) %in%
                        paste(ancho$LocationAbbr, ancho$Anio), ]
linea(sprintf("5e. Esperadas %d combinaciones estado-ano (%d x %d); faltan %d por completo: %s",
              nrow(esperadas), length(unique(tot$LocationAbbr)), length(anos_pa), nrow(ausentes),
              paste(ausentes$LocationAbbr, ausentes$Anio, collapse = ", ")))
linea("    (el CDC no publico esos estado-ano: sin la clase no se puede imputar -> quedan fuera)")
incompletas <- ancho[!complete.cases(ancho), c("LocationAbbr", "Anio")]
linea(sprintf("    Filas con algun indicador faltante tras el filtro de calidad: %d", nrow(incompletas)))
ancho <- ancho[complete.cases(ancho), ]
registrar("P10", "Eliminar estado-ano incompletos", "ancho[complete.cases(ancho), ]", ancho)

# 5f. discretizacion de la clase
ancho$nivel_obesidad <- cut(ancho$obesidad, breaks = c(-Inf, 30, 35, Inf), right = FALSE,
                            labels = c("Baja", "Media", "Alta"))
linea("5f. Clase: nivel_obesidad = Baja (<30), Media [30,35), Alta (>=35):")
print(table(ancho$nivel_obesidad))
print(table(Anio = ancho$Anio, Nivel = ancho$nivel_obesidad))

# 5g. atipicos (regla de Tukey 1.5*IQR) - se reportan, no se eliminan (son estados reales)
linea()
linea("5g. Atipicos por regla de Tukey (1.5*IQR):")
predictores <- c("aerobica_150", "aerobica150_y_fuerza", "aerobica_300", "fuerza_2dias", "inactividad")
for (v in c("obesidad", predictores)) {
  q <- quantile(ancho[[v]], c(.25, .75))
  li <- q[1] - 1.5 * diff(q)
  ls <- q[2] + 1.5 * diff(q)
  at <- which(ancho[[v]] < li | ancho[[v]] > ls)
  linea(sprintf("  %-22s limites [%.1f, %.1f]  atipicos: %s", v, li, ls,
                if (length(at)) paste0(ancho$LocationAbbr[at], "-", ancho$Anio[at], collapse = ", ") else "ninguno"))
}
linea("  Se conservan: son mediciones validas de estados reales (p. ej., DC o CO con alta actividad).")

# 5h. normalizacion min-max de predictores (para metodos basados en distancia)
norm <- ancho
for (v in predictores) norm[[v]] <- (ancho[[v]] - min(ancho[[v]])) / (max(ancho[[v]]) - min(ancho[[v]]))
linea()
linea("5h. Normalizacion min-max [0,1] de los predictores (vista_minable_normalizada.csv).")

linea()
linea("Correlacion de cada predictor con el % de obesidad:")
print(round(cor(ancho[, c(predictores, "Anio")], ancho$obesidad), 3))
linea()
linea("Resumen de la vista minable:")
print(summary(ancho[, c("Anio", "obesidad", predictores, "nivel_obesidad")]))
write.csv(ancho, file.path(salidas, "vista_minable.csv"), row.names = FALSE)
write.csv(norm, file.path(salidas, "vista_minable_normalizada.csv"), row.names = FALSE)

# -----------------------------------------------------------------------------
# 6. SUBCONJUNTOS PARA EL OBJETIVO SECUNDARIO (descriptivo)
# -----------------------------------------------------------------------------
titulo("6. SUBCONJUNTOS DESCRIPTIVOS: PERFIL SOCIOECONOMICO DE LA OBESIDAD")
ultimo <- max(d$Anio[d$QuestionID == "Q036"])
ob <- subset(d, QuestionID == "Q036" & Anio == ultimo,
             select = c(LocationAbbr, StratificationCategory1, Stratification1, Data_Value, Sample_Size))
registrar("P11", sprintf("Obesidad %d, todos los estratos", ultimo),
          "subset(d, QuestionID=='Q036' & Anio==ultimo, select=...)", ob)
write.csv(ob, file.path(salidas, sprintf("obesidad_%d_estratos_detalle.csv", ultimo)), row.names = FALSE)
por_cat <- split(ob, ob$StratificationCategory1)  # subsetting por GRUPO
linea(sprintf("Mediana entre estados del %% de obesidad en %d por estrato:", ultimo))
resumen_estratos <- do.call(rbind, lapply(names(por_cat), function(k) {
  s <- por_cat[[k]]
  a <- aggregate(Data_Value ~ Stratification1, data = s, FUN = median)
  n <- aggregate(Data_Value ~ Stratification1, data = s, FUN = length)
  data.frame(Categoria = k, Estrato = a$Stratification1, Mediana_obesidad = a$Data_Value,
             Estados_con_dato = n$Data_Value)
}))
orden_ing <- c("Less than $15,000", "$15,000 - $24,999", "$25,000 - $34,999", "$35,000 - $49,999",
               "$50,000 - $74,999", "$75,000 or greater", "Data not reported")
orden_edu <- c("Less than high school", "High school graduate", "Some college or technical school",
               "College graduate")
for (k in c("Income", "Education", "Age (years)", "Sex", "Race/Ethnicity")) {
  s <- resumen_estratos[resumen_estratos$Categoria == k, ]
  if (k == "Income") s <- s[match(orden_ing, s$Estrato), ]
  if (k == "Education") s <- s[match(orden_edu, s$Estrato), ]
  linea("  ", k, ":")
  for (i in seq_len(nrow(s)))
    linea(sprintf("     %-36s %5.1f %%   (%d estados)", s$Estrato[i], s$Mediana_obesidad[i], s$Estados_con_dato[i]))
}
write.csv(resumen_estratos, file.path(salidas, sprintf("obesidad_por_estrato_%d.csv", ultimo)), row.names = FALSE)

# top-n con order/head
tot_ult <- ob[ob$StratificationCategory1 == "Total", ]
tot_ult <- tot_ult[order(-tot_ult$Data_Value), ]
linea()
linea(sprintf("Top 5 estados con mayor obesidad en %d: %s", ultimo,
              paste(sprintf("%s %.1f%%", head(tot_ult$LocationAbbr, 5), head(tot_ult$Data_Value, 5)), collapse = ", ")))
linea(sprintf("Top 5 con menor obesidad en %d:      %s", ultimo,
              paste(sprintf("%s %.1f%%", tail(tot_ult$LocationAbbr, 5), tail(tot_ult$Data_Value, 5)), collapse = ", ")))

# -----------------------------------------------------------------------------
# 7. COMPROBACION: la vista minable sirve al objetivo (muestreo aleatorio 70/30)
# -----------------------------------------------------------------------------
titulo("7. COMPROBACION DE LA VISTA MINABLE (muestreo aleatorio 70/30 + arbol rpart)")
set.seed(1851265)
idx <- sample(nrow(ancho), round(0.7 * nrow(ancho)))  # subsetting ALEATORIO
entrena <- ancho[idx, ]
prueba <- ancho[-idx, ]
registrar("P12", "Muestra de entrenamiento (70 %)", "ancho[sample(n, 0.7n), ]", entrena)
registrar("P13", "Muestra de prueba (30 %)", "ancho[-idx, ]", prueba)
modelo <- rpart(nivel_obesidad ~ aerobica_150 + aerobica150_y_fuerza + aerobica_300 + fuerza_2dias +
                  inactividad + Anio, data = entrena, method = "class")
print(modelo)
pred <- predict(modelo, prueba, type = "class")
linea(sprintf("Exactitud en prueba: %.1f%%  (clase mayoritaria 'Baja' = %.1f%%)",
              100 * mean(pred == prueba$nivel_obesidad), 100 * mean(prueba$nivel_obesidad == "Baja")))
print(table(Real = prueba$nivel_obesidad, Prediccion = pred))
linea("Importancia de variables:")
print(round(modelo$variable.importance, 1))

# -----------------------------------------------------------------------------
# 8. GRAFICAS Y BITACORA
# -----------------------------------------------------------------------------
est_tot <- d[d$StratificationCategory1 == "Total" & d$QuestionID == "Q036", ]
png(file.path(salidas, "fig1_tendencia_obesidad.png"), width = 1600, height = 800, res = 170)
par(mar = c(4.2, 4.2, 3, 1))
boxplot(Data_Value ~ Anio, data = est_tot, col = "#DCE8F7", border = "#2F5D8A",
        xlab = "Año", ylab = "% de adultos con obesidad",
        main = "Obesidad adulta por estado, 2011-2025 (50 estados + DC, estrato Total)")
abline(h = c(30, 35), lty = 2, col = c("#8A6D1F", "#B04A2F"))
legend("topleft", c("corte 30 % (Baja/Media)", "corte 35 % (Media/Alta)"), lty = 2,
       col = c("#8A6D1F", "#B04A2F"), bty = "n", cex = 0.8)
invisible(dev.off())

png(file.path(salidas, "fig2_inactividad_vs_obesidad.png"), width = 1400, height = 950, res = 170)
par(mar = c(4.2, 4.2, 3, 1))
col_nivel <- c(Baja = "#4C9A5B", Media = "#D08A2E", Alta = "#B04A2F")
plot(ancho$inactividad, ancho$obesidad, pch = 19, col = col_nivel[as.character(ancho$nivel_obesidad)],
     xlab = "% sin actividad física en tiempo libre (Q047)", ylab = "% con obesidad (Q036)",
     main = sprintf("Vista minable: inactividad vs. obesidad (r = %.2f)", cor(ancho$inactividad, ancho$obesidad)))
abline(lm(obesidad ~ inactividad, data = ancho), lwd = 2)
legend("topleft", names(col_nivel), col = col_nivel, pch = 19, bty = "n", title = "Nivel")
invisible(dev.off())

ing <- resumen_estratos[resumen_estratos$Categoria == "Income", ]
ing <- ing[match(orden_ing[1:6], ing$Estrato), ]
edu <- resumen_estratos[resumen_estratos$Categoria == "Education", ]
edu <- edu[match(orden_edu, edu$Estrato), ]
png(file.path(salidas, "fig3_obesidad_ingreso_escolaridad.png"), width = 1800, height = 800, res = 170)
par(mfrow = c(1, 2), mar = c(7.5, 4.2, 3, 1))
b <- barplot(ing$Mediana_obesidad, names.arg = c("<15k", "15-25k", "25-35k", "35-50k", "50-75k", ">=75k"),
             col = "#DCE8F7", border = "#2F5D8A", ylim = c(0, 45), las = 2,
             ylab = "% obesidad (mediana entre estados)", main = sprintf("Por ingreso anual (USD), %d", ultimo))
text(b, ing$Mediana_obesidad + 2, sprintf("%.1f", ing$Mediana_obesidad), cex = 0.8)
b <- barplot(edu$Mediana_obesidad, names.arg = c("< Prepa", "Prepa", "Univ. trunca", "Universidad"),
             col = "#EFE0F5", border = "#6B4A7A", ylim = c(0, 45), las = 2,
             main = sprintf("Por escolaridad, %d", ultimo))
text(b, edu$Mediana_obesidad + 2, sprintf("%.1f", edu$Mediana_obesidad), cex = 0.8)
invisible(dev.off())

titulo("8. BITACORA DEL TRATAMIENTO")
print(bitacora, right = FALSE, row.names = FALSE)
write.csv(bitacora, file.path(salidas, "bitacora_tratamiento.csv"), row.names = FALSE)
linea()
linea("Archivos en ", salidas, ": ", paste(list.files(salidas), collapse = ", "))
sink()
