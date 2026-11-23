# =============================================================================
# REGRESION STEPWISE CON AIC (OD/AM R.pdf p.20-24)
# p.20: hacia adelante, hacia atras o bidireccional; p.21-22: AIC = 2k - 2 ln(L), menor es mejor.
# T9: las laminas cargan library(MASSExtra); stepAIC es la funcion de MASS que MASSExtra reexporta.
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ARCHIVO   <- "BR.csv"      # "Boston.csv" con DATASET <- "Boston" (p.23)
DATASET   <- ""            # "Boston": data(Boston) del paquete MASS
Y         <- "precio"
DIRECCION <- "both"        # "both", "backward" o "forward"
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
suppressMessages(library(MASSExtra))   # p.23-24 (T9)

if (DATASET == "Boston") {
  data(Boston)
  data <- Boston
  write.csv(data, file.path(base, "datos", ARCHIVO), row.names = FALSE)   # el oraculo lee el mismo CSV
} else {
  data <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE)
}

# ---- p.23-24: modelo completo y stepwise bidireccional con AIC
full_model <- lm(as.formula(paste0("`", Y, "` ~ .")), data = data)
print(summary(full_model))
if (DIRECCION == "forward") {
  vacio <- lm(as.formula(paste0("`", Y, "` ~ 1")), data = data)
  step_model <- stepAIC(vacio, scope = list(lower = ~1, upper = formula(full_model)), direction = "forward", trace = FALSE)
} else {
  step_model <- stepAIC(full_model, direction = DIRECCION, trace = FALSE)
}
print(step_model$anova)
print(summary(step_model))

# ---- Exportes para la verificacion
an <- step_model$anova
write.csv(data.frame(paso = an$Step, Df = an$Df, Deviance = an$Deviance, gl_resid = an[["Resid. Df"]],
                     RSS = an[["Resid. Dev"]], AIC = an$AIC), file.path(base, "pasos_R.csv"), row.names = FALSE)
cf <- coef(step_model)
write.csv(data.frame(termino = names(cf), coef = unname(cf)), file.path(base, "final_R.csv"), row.names = FALSE)
# Vecindad del modelo final: quitar o agregar una sola variable no debe bajar el AIC (p.20-22)
d1 <- drop1(step_model)
a1 <- add1(step_model, scope = formula(full_model))
vec <- rbind(data.frame(cambio = paste("-", rownames(d1)), Df = d1$Df, RSS = d1$RSS, AIC = d1$AIC),
             data.frame(cambio = paste("+", rownames(a1)[-1]), Df = a1$Df[-1], RSS = a1$RSS[-1], AIC = a1$AIC[-1]))
vec$cambio[1] <- "<none>"
write.csv(vec, file.path(base, "vecinos_R.csv"), row.names = FALSE)
ea <- extractAIC(step_model)
write.csv(data.frame(n = nrow(data), edf = ea[1], extractAIC = ea[2], AIC_logLik = AIC(step_model),
                     logLik = as.numeric(logLik(step_model)), R2 = summary(step_model)$r.squared,
                     R2_aj = summary(step_model)$adj.r.squared, AIC_completo = extractAIC(full_model)[2]),
          file.path(base, "resumen_R.csv"), row.names = FALSE)
cat(sprintf("Modelo final: %d parametros, extractAIC = %.6f, AIC() = 2k - 2 ln L = %.6f\n", ea[1], ea[2], AIC(step_model)))
