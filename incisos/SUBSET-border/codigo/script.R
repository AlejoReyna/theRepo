# ============================================================================
# TRATAMIENTO DE DATOS: SUBSET.pdf p.12-15: Border Crossing
# Objetivo de mineria: Subconjuntos de las láminas
# Generado desde datos/plan.json (el mismo plan que ejecuta codigo/resolver.py)
# Modismos de SUBSET.pdf: read.csv, subset, df[, c()], indice negativo, which, %in%,
# grepl, complete.cases, is.na, colSums(is.na()), write.csv
# ============================================================================
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
crudo <- read.csv(file.path(base, "datos", "Border_Crossing_Entry_Data.csv"), check.names = FALSE, na.strings = c("", "NA"),
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
# B1. State == Texas (p.12)
B1 <- subset(P0, State == "Texas")
registrar("B1", "State == Texas (p.12)", B1)
print(head(B1, 3))
# B2. Texas y Trucks (p.13)
B2 <- subset(P0, (State == "Texas" & Measure == "Trucks"))
registrar("B2", "Texas y Trucks (p.13)", B2)
print(head(B2, 3))
# B3. df[, c(Port Name, Value)] (p.13)
B3 <- P0[, c("Port Name", "Value")]
registrar("B3", "df[, c(Port Name, Value)] (p.13)", B3)
print(head(B3, 3))
# B4. Arizona con select (p.14)
B4 <- subset(P0, State == "Arizona", select = c("Port Name", "Value"))
registrar("B4", "Arizona con select (p.14)", B4)
print(head(B4, 3))
# B5. State != Texas (p.14)
B5 <- subset(P0, State != "Texas")
registrar("B5", "State != Texas (p.14)", B5)
print(head(B5, 3))
# B6. Texas o Arizona (p.15)
B6 <- subset(P0, (State == "Texas" | State == "Arizona"))
registrar("B6", "Texas o Arizona (p.15)", B6)
print(head(B6, 3))
# B7. 500 <= Value <= 5000 (p.15)
B7 <- subset(P0, (Value >= 500 & Value <= 5000))
registrar("B7", "500 <= Value <= 5000 (p.15)", B7)
print(head(B7, 3))
write.csv(bitacora, file.path(base, "bitacora_R.csv"), row.names = FALSE)
cat("\nBitacora:\n"); print(bitacora, row.names = FALSE)
