# ============================================================================
# TRATAMIENTO DE DATOS: SUBSET.pdf p.16-17: MTA Metro-North
# Objetivo de mineria: Subconjuntos de las láminas
# Generado desde datos/plan.json (el mismo plan que ejecuta codigo/resolver.py)
# Modismos de SUBSET.pdf: read.csv, subset, df[, c()], indice negativo, which, %in%,
# grepl, complete.cases, is.na, colSums(is.na()), write.csv
# ============================================================================
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
crudo <- read.csv(file.path(base, "datos", "MTA_Metro-North_Delay_Verification__Beginning_2012.csv"), check.names = FALSE, na.strings = c("", "NA"),
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
# M1. data[data[,8] == Off-Peak, ] (p.16)
M1 <- P0[which(P0[["Period"]] == "Off-Peak"), ]
registrar("M1", "data[data[,8] == Off-Peak, ] (p.16)", M1)
print(head(M1, 3))
# M2. subset(op, Status == Cancelled) (p.16)
M2 <- subset(M1, Status == "Cancelled")
registrar("M2", "subset(op, Status == Cancelled) (p.16)", M2)
print(head(M2, 3))
# M3. Fecha > 2024-01-01, 10 < retraso <= 20, Grand Central (p.17)
M3 <- subset(P0, (as.Date(`Service Date`, format = "%m/%d/%Y") > as.Date("2024-01-01") & `Minutes Late` > 10 & `Minutes Late` <= 20 & !is.na(`Minutes Late`) & (`Arrive Station` == "Grand Central Terminal" | `Depart Station` == "Grand Central Terminal")))
registrar("M3", "Fecha > 2024-01-01, 10 < retraso <= 20, Grand Central (p.17)", M3)
print(head(M3, 3))
write.csv(bitacora, file.path(base, "bitacora_R.csv"), row.names = FALSE)
cat("\nBitacora:\n"); print(bitacora, row.names = FALSE)
