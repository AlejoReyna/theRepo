# ============================================================================
# TRATAMIENTO DE DATOS: MC AD26 problema 2: tratamiento de export.csv con subsettings variados
# Objetivo de mineria: Clasificar el nivel de obesidad adulta (Baja < 30 %, Media 30-35 %, Alta >= 35 %) de cada estado x año con sus indicadores de actividad física (Q043-Q047)
# Generado desde datos/plan.json (el mismo plan que ejecuta codigo/resolver.py)
# Modismos de SUBSET.pdf: read.csv, subset, df[, c()], indice negativo, which, %in%,
# grepl, complete.cases, is.na, colSums(is.na()), write.csv
# ============================================================================
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
crudo <- read.csv(file.path(base, "datos", "export.csv"), check.names = FALSE, na.strings = c("", "NA"),
                  stringsAsFactors = FALSE)
names(crudo) <- trimws(names(crudo))
bitacora <- data.frame(paso = character(0), operacion = character(0), filas = integer(0), columnas = integer(0))
registrar <- function(paso, operacion, d) {
  bitacora[nrow(bitacora) + 1, ] <<- list(paso, operacion, nrow(d), ncol(d))
  cat(sprintf("%-4s %-60s %8d filas %3d columnas\n", paso, operacion, nrow(d), ncol(d)))
}
cat("Faltantes por columna (colSums(is.na())):\n"); print(colSums(is.na(crudo)))
P0 <- crudo
registrar("P0", "Carga del archivo original", P0)
# P1. Eliminar columnas constantes, duplicadas, dispersas y códigos
P1 <- P0[, -which(names(P0) %in% c("YearEnd", "Datasource", "Topic", "Question", "Data_Value_Unit", "Data_Value_Type", "Data_Value_Alt", "Data_Value_Footnote", "Total", "Age(years)", "Education", "Sex", "Income", "Race/Ethnicity", "ClassID", "TopicID", "DataValueTypeID", "LocationID", "StratificationCategoryId1", "StratificationID1"))]   # indice negativo por nombre
registrar("P1", "Eliminar columnas constantes, duplicadas, dispersas y códigos", P1)
print(head(P1, 3))
# P2a. Sample_Size: texto con comas -> número
P2a <- P1
P2a[["Sample_Size"]] <- as.numeric(gsub(",", "", P2a[["Sample_Size"]]))
registrar("P2a", "Sample_Size: texto con comas -> número", P2a)
print(head(P2a, 3))
# P2b. GeoLocation -> Latitud y Longitud
P2b <- P2a
m <- regmatches(P2b[["GeoLocation"]], regexec("\\(\\s*([-0-9.]+),\\s*([-0-9.]+)\\)", P2b[["GeoLocation"]]))
P2b[["Latitud"]] <- as.numeric(sapply(m, function(x) if (length(x) > 1) x[2] else NA))
P2b[["Longitud"]] <- as.numeric(sapply(m, function(x) if (length(x) > 2) x[3] else NA))
P2b[["GeoLocation"]] <- NULL
registrar("P2b", "GeoLocation -> Latitud y Longitud", P2b)
print(head(P2b, 3))
# P2c. Ancho_IC = High - Low
P2c <- P2b
P2c[["Ancho_IC"]] <- P2c[["High_Confidence_Limit"]] - P2c[["Low_Confidence_Limit"]]
registrar("P2c", "Ancho_IC = High - Low", P2c)
print(head(P2c, 3))
# P2. YearStart -> Anio
P2 <- P2c
names(P2)[names(P2) == "YearStart"] <- "Anio"
registrar("P2", "YearStart -> Anio", P2)
print(head(P2, 3))
# P3a. Quitar filas sin valor (suprimidas por muestra insuficiente)
P3a <- subset(P2, !is.na(Data_Value))
registrar("P3a", "Quitar filas sin valor (suprimidas por muestra insuficiente)", P3a)
print(head(P3a, 3))
# P3. Quitar el símbolo de supresión (ya constante)
P3 <- P3a[, -which(names(P3a) %in% c("Data_Value_Footnote_Symbol"))]   # indice negativo por nombre
registrar("P3", "Quitar el símbolo de supresión (ya constante)", P3)
print(head(P3, 3))
# P4. Solo 50 estados + DC
P4 <- P3[which(!(P3[["LocationAbbr"]] %in% c("US", "GU", "PR", "VI"))), ]
registrar("P4", "Solo 50 estados + DC", P4)
print(head(P4, 3))
# P5. Quitar estimaciones imprecisas (IC > 20)
idx <- which(P4[["Ancho_IC"]] > 20)
P5 <- if (length(idx)) P4[-idx, ] else P4   # -integer(0) borraria todo
registrar("P5", "Quitar estimaciones imprecisas (IC > 20)", P5)
print(head(P5, 3))
# P6. Estrato Total (nivel estatal)
P6 <- P5[which(P5[["StratificationCategory1"]] == "Total"), ]
registrar("P6", "Estrato Total (nivel estatal)", P6)
print(head(P6, 3))
# P7. Obesidad (Q036) y actividad física (Q043-Q047)
P7 <- P6[which((grepl("Obesity|Physical Activity", P6[["Class"]]) & P6[["QuestionID"]] != "Q037")), ]
registrar("P7", "Obesidad (Q036) y actividad física (Q043-Q047)", P7)
print(head(P7, 3))
# P8. Años con todas las preguntas
comunes <- Reduce(intersect, split(P7[["Anio"]], P7[["QuestionID"]]))
P8 <- P7[P7[["Anio"]] %in% comunes, ]
registrar("P8", "Años con todas las preguntas", P8)
print(head(P8, 3))
# P9. Pivoteo largo -> ancho (reshape)
P9 <- reshape(P8[, c("LocationAbbr", "LocationDesc", "Anio", "QuestionID", "Data_Value")], idvar = c("LocationAbbr", "LocationDesc", "Anio"), timevar = "QuestionID", direction = "wide")
registrar("P9", "Pivoteo largo -> ancho (reshape)", P9)
print(head(P9, 3))
# P10. Eliminar estado-año incompletos
P10 <- P9[complete.cases(P9), ]
write.csv(P10, file.path(base, "vista_minable.csv"), row.names = FALSE)
registrar("P10", "Eliminar estado-año incompletos", P10)
print(head(P10, 3))
# P11. Obesidad 2025, todos los estratos
P11 <- subset(P5, (QuestionID == "Q036" & Anio == 2025), select = c("LocationAbbr", "StratificationCategory1", "Stratification1", "Data_Value", "Sample_Size"))
registrar("P11", "Obesidad 2025, todos los estratos", P11)
print(head(P11, 3))
# P10c. Clase nivel_obesidad con cut()
P10c <- P10
P10c[["nivel_obesidad"]] <- as.character(cut(P10c[["Data_Value.Q036"]], breaks = c(-Inf, 30, 35, Inf), right = FALSE, labels = c("Baja", "Media", "Alta")))
registrar("P10c", "Clase nivel_obesidad con cut()", P10c)
print(head(P10c, 3))
# P12. Muestra de entrenamiento (70 %)
set.seed(1851265)
idx <- sample(nrow(P10c), round(0.7 * nrow(P10c)))
P12 <- P10c[idx, ]
registrar("P12", "Muestra de entrenamiento (70 %)", P12)
print(head(P12, 3))
# P13. Muestra de prueba (30 %)
set.seed(1851265)
idx <- sample(nrow(P10c), round(0.7 * nrow(P10c)))
P13 <- P10c[-idx, ]
registrar("P13", "Muestra de prueba (30 %)", P13)
print(head(P13, 3))
write.csv(bitacora, file.path(base, "bitacora_R.csv"), row.names = FALSE)
cat("\nBitacora:\n"); print(bitacora, row.names = FALSE)
