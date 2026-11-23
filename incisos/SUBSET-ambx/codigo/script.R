# ============================================================================
# TRATAMIENTO DE DATOS: SUBSET.pdf p.5-8: ambx (airquality)
# Objetivo de mineria: Quitar faltantes
# Generado desde datos/plan.json (el mismo plan que ejecuta codigo/resolver.py)
# Modismos de SUBSET.pdf: read.csv, subset, df[, c()], indice negativo, which, %in%,
# grepl, complete.cases, is.na, colSums(is.na()), write.csv
# ============================================================================
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
crudo <- read.csv(file.path(base, "datos", "ambx.csv"), check.names = FALSE, na.strings = c("", "NA"),
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
# A1. Ozone sin NA (p.5-6)
A1 <- P0[complete.cases(P0[, c("Ozone")]), ]
registrar("A1", "Ozone sin NA (p.5-6)", A1)
print(head(A1, 3))
# A2. complete.cases(ozone, solar) (p.7-8)
A2 <- P0[complete.cases(P0[, c("Ozone", "Solar.R")]), ]
registrar("A2", "complete.cases(ozone, solar) (p.7-8)", A2)
print(head(A2, 3))
# A3. complete.cases(datos) (p.9)
A3 <- P0[complete.cases(P0), ]
write.csv(A3, file.path(base, "datos_limpios.csv"), row.names = FALSE)
registrar("A3", "complete.cases(datos) (p.9)", A3)
print(head(A3, 3))
write.csv(bitacora, file.path(base, "bitacora_R.csv"), row.names = FALSE)
cat("\nBitacora:\n"); print(bitacora, row.names = FALSE)
