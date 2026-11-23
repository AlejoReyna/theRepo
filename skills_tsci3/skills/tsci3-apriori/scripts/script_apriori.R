# =============================================================================
# REGLAS DE ASOCIACION CON arules (estructura de OD/arules R (2).txt)
# Ejecutar: Rscript codigo/script.R        (desde la carpeta del problema)
# =============================================================================
ARCHIVO   <- "datos.csv"
COLUMNAS  <- NULL            # NULL = todas
SOPORTE   <- 0.01            # umbrales del curso (arules R (2).txt)
CONFIANZA <- 0.1

suppressPackageStartupMessages({ library(arules); library(arulesViz); library(RColorBrewer) })
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()

# T22: las celdas vacias se leen como NA; si no, arules crea items "columna=" que aparecen
# en casi todas las filas (con apri poko.csv el script del curso se queda sin memoria)
df <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE, na.strings = c("", "NA"))
if (!is.null(COLUMNAS)) df <- df[, COLUMNAS, drop = FALSE]
df[] <- lapply(df, factor)
trans <- as(df, "transactions")
print(head(trans)); print(summary(trans))
rules <- apriori(trans, parameter = list(supp = SOPORTE, conf = CONFIANZA), control = list(verbose = FALSE))
cat(sprintf("\nReglas: %d (con antecedente vacio: %d)\n", length(rules), sum(size(lhs(rules)) == 0)))
inspect(head(sort(rules, by = "lift"), 10))
png(file.path(base, "frecuencia_items.png"), width = 900, height = 600)
arules::itemFrequencyPlot(trans, topN = 20, col = brewer.pal(8, "Pastel2"), main = "Relative Item Frequency Plot",
                          type = "relative", ylab = "Item Frequency (Relative)")
invisible(dev.off())
rules_df <- as(rules, "data.frame")
write.csv(rules_df, file = file.path(base, "association_rules.csv"), row.names = FALSE)
