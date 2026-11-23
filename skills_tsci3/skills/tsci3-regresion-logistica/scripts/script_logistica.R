# =============================================================================
# REGRESION LOGISTICA BINARIA Y MULTINOMIAL (OD/AM R.pdf p.37-41)
# p.37: sigmoide p = 1 / (1 + e^-(b0 + b1x1 + ... + bnxn)); p.38: binaria y multinomial; p.39: VIF.
# T10: las laminas ya usan los nombres de OD/BR (2).csv en p.40-41 (baños, m2_construcción, m2_terreno).
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ARCHIVO <- "BR.csv"
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
suppressMessages({library(glmnet); library(car); library(nnet)})

df <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE)

# ---- p.40: logistica binaria
median_precio <- median(df$precio)
df$precio_alto <- as.integer(df$precio > median_precio)
model <- glm(precio_alto ~ recamaras + baños + m2_construcción + m2_terreno, data = df, family = binomial)
print(summary(model))
an <- Anova(model)
print(an)
v <- vif(model)     # multicollinearity (variance inflation factor)
print(v)
new_data <- data.frame(recamaras = 3, baños = 2, m2_construcción = 120, m2_terreno = 200)
p_bin <- predict(model, newdata = new_data, type = "response")
cat("P(precio_alto = 1 | nuevos) =", p_bin, "\n")

# ---- p.41: logistica multinomial
percentile_33 <- quantile(df$precio, 0.33)
percentile_66 <- quantile(df$precio, 0.66)
df$categoria_precio <- cut(df$precio, breaks = c(-Inf, percentile_33, percentile_66, Inf),
                           labels = c("bajo", "medio", "alto"), right = FALSE)
print(table(df$categoria_precio))
model_multinom <- multinom(categoria_precio ~ recamaras + baños + m2_construcción + m2_terreno, data = df)
print(summary(model_multinom))
coefficients <- coef(model_multinom)
intercepts <- model_multinom$wts[1:nlevels(df$categoria_precio)]
print(coefficients)
print(intercepts)   # T25: son pesos de la clase base (0, 0, 0), no los interceptos; estos son coefficients[, 1]
predicted_probabilities <- predict(model_multinom, newdata = new_data, type = "probs")
print(predicted_probabilities)

# ---- Exportes para la verificacion
write.csv(data.frame(termino = names(coef(model)), coef = unname(coef(model)), SE = summary(model)$coefficients[, 2]),
          file.path(base, "coef_bin_R.csv"), row.names = FALSE)
write.csv(data.frame(termino = rownames(an), LR = an[, 1], gl = an[, 2], p = an[, 3]), file.path(base, "anova_R.csv"), row.names = FALSE)
write.csv(data.frame(termino = names(v), VIF = unname(v)), file.path(base, "vif_R.csv"), row.names = FALSE)
cm <- coefficients
write.csv(data.frame(categoria = rep(rownames(cm), ncol(cm)), termino = rep(colnames(cm), each = nrow(cm)), coef = as.vector(cm)),
          file.path(base, "coef_multi_R.csv"), row.names = FALSE)
write.csv(data.frame(mediana = median_precio, p33 = unname(percentile_33), p66 = unname(percentile_66),
                     n_alto_bin = sum(df$precio_alto), n_bajo = sum(df$categoria_precio == "bajo"),
                     n_medio = sum(df$categoria_precio == "medio"), n_alto = sum(df$categoria_precio == "alto"),
                     p_bin = unname(p_bin), deviance_bin = deviance(model), iter_bin = model$iter,
                     prob_bajo = unname(predicted_probabilities["bajo"]), prob_medio = unname(predicted_probabilities["medio"]),
                     prob_alto = unname(predicted_probabilities["alto"]), loglik_multi = as.numeric(logLik(model_multinom)),
                     convergencia_multi = model_multinom$convergence,
                     wts_1 = intercepts[1], wts_2 = intercepts[2], wts_3 = intercepts[3]),
          file.path(base, "resumen_R.csv"), row.names = FALSE)
