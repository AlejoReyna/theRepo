# =============================================================================
# REGRESION LINEAL SIMPLE CON PREDICTOR BINARIO (OD/AM R.pdf p.11-12)
# Ejecutar: Rscript codigo/script.R
# =============================================================================
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
model <- lm(mpg ~ am, data = mtcars)                                  # p.11
print(summary(model))
tt <- t.test(mpg ~ am, data = mtcars, var.equal = TRUE)              # p.11
print(tt)
mtcars$automatic <- ifelse(mtcars$am == 0, "yes", "no")              # p.12
model2 <- lm(mpg ~ factor(automatic), data = mtcars)
print(model2)
s <- summary(model)
write.csv(data.frame(b0 = coef(model)[1], b1 = coef(model)[2], SE_b1 = s$coefficients[2, 2], t = s$coefficients[2, 3],
                     p = s$coefficients[2, 4], R2 = s$r.squared, t_ttest = unname(tt$statistic), p_ttest = tt$p.value,
                     b0_factor = coef(model2)[1], b1_factor = coef(model2)[2]),
          file.path(base, "binario_R.csv"), row.names = FALSE)
