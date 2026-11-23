# =============================================================================
# MINIMOS CUADRADOS EN R (OD/AM R.pdf p.6)
# Ejecutar: Rscript codigo/script.R        (desde la carpeta del problema)
# =============================================================================
ARCHIVO <- "old.csv"
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)

data <- read.csv(file.path(base, "datos", ARCHIVO))
modelo <- lm(data$waiting ~ data$eruptions, data = data)       # p.6
print(summary(modelo))
png(file.path(base, "recta.png"), width = 800, height = 550)
plot(data$eruptions, data$waiting, xlab = "eruptions", ylab = "waiting", main = "Mínimos cuadrados")
abline(modelo)                                                  # p.6
invisible(dev.off())
s <- summary(modelo)
rss <- sum(residuals(modelo)^2)
salida <- data.frame(b = coef(modelo)[1], m = coef(modelo)[2], SE_b = s$coefficients[1, 2], SE_m = s$coefficients[2, 2],
                     t_m = s$coefficients[2, 3], p_m = s$coefficients[2, 4], R2 = s$r.squared, R2_ajustado = s$adj.r.squared,
                     F = s$fstatistic[1], sigma = s$sigma, RSS = rss, MSE = rss / nrow(data))
print(salida, row.names = FALSE)
write.csv(salida, file.path(base, "minimos_R.csv"), row.names = FALSE)
