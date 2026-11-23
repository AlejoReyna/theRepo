# =============================================================================
# PRUEBA DE BREUSCH-PAGAN (OD/AM R.pdf p.7-9)
# H0: homocedasticidad; HA: heterocedasticidad. Se rechaza H0 si p < alfa (0.05, p.8).
# bptest es del paquete lmtest (la lamina no lo carga).
# Ejecutar: Rscript codigo/script.R
# =============================================================================
suppressPackageStartupMessages(library(lmtest))
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
ALFA <- 0.05
prueba <- function(modelo, nombre) {
  bp <- bptest(modelo)                                                 # p.9
  print(bp)
  decision <- ifelse(bp$p.value < ALFA, "se rechaza H0: hay heterocedasticidad", "no se rechaza H0: homocedasticidad")
  cat(nombre, "->", decision, "\n\n")
  data.frame(modelo = nombre, BP = unname(bp$statistic), gl = unname(bp$parameter), p = bp$p.value,
             predictores = length(coef(modelo)) - 1, decision = decision)
}
old <- read.csv(file.path(base, "datos", "old.csv"))
m1 <- lm(waiting ~ eruptions, data = old)
br <- read.csv(file.path(base, "datos", "BR.csv"), check.names = FALSE)
m2 <- lm(precio ~ m2_construcción + recamaras + condición, data = br)
res <- rbind(prueba(m1, "old: waiting ~ eruptions"), prueba(m2, "BR: precio ~ m2_construcción + recamaras + condición"))
print(res, row.names = FALSE)
write.csv(res, file.path(base, "bp_R.csv"), row.names = FALSE)
