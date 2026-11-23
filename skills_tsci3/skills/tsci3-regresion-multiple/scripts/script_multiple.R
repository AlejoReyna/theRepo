# =============================================================================
# REGRESION MULTIPLE Y PREDICTOR NO BINARIO (OD/AM R.pdf p.25-28, p.34-35)
# T10: las laminas usan tcons, recamaras, condicion, tterreno, numban; en BR (2).csv son
#      m2_construcción, recamaras, condición, m2_terreno, baños.
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ARCHIVO <- "BR.csv"
SEMILLA <- 1851265          # T15: p.25-27 no fija semilla para la division 80/20
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)

data <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE)
# ---- p.28: modelo, summary y prediccion con datos nuevos
model <- lm(precio ~ m2_construcción + recamaras + condición, data = data)
print(summary(model))
new_data <- data.frame(m2_construcción = 130, recamaras = 3, condición = 4)
pred <- predict(model, new_data)
cat("predict(model, new_data) =", pred, "\n")
cf <- coef(model)
write.csv(data.frame(termino = names(cf), coef = unname(cf), SE = unname(summary(model)$coefficients[, 2][names(cf)])),
          file.path(base, "coef_R.csv"), row.names = FALSE)

# ---- p.25-27: entrenamiento 80 %, prueba 20 %, MSE, MAE y R2 en prueba
set.seed(SEMILLA)
idx <- sample(nrow(data), 0.8 * nrow(data))
train <- data[idx, ]; test <- data[-idx, ]
m_tr <- lm(precio ~ m2_construcción + recamaras + condición, data = train)
y_pred <- predict(m_tr, test)
mse <- mean((test$precio - y_pred)^2); mae <- mean(abs(test$precio - y_pred))
r2 <- 1 - sum((test$precio - y_pred)^2) / sum((test$precio - mean(test$precio))^2)
cat(sprintf("Prueba (20 %%): MSE = %.6f, MAE = %.6f, R2 = %.6f\n", mse, mae, r2))
write.csv(data.frame(fila = setdiff(seq_len(nrow(data)), idx), y = test$precio, y_pred = y_pred), file.path(base, "prueba_R.csv"), row.names = FALSE)

# ---- p.34-35: predictor no binario como factor
datos <- data
datos$condición <- as.factor(datos$condición)
datos$recamaras <- as.factor(datos$recamaras)
modelo <- lm(precio ~ m2_construcción + condición + m2_terreno + baños + recamaras, data = datos)
print(summary(modelo))
write.csv(data.frame(termino = names(coef(modelo)), coef = unname(coef(modelo))), file.path(base, "coef_factor_R.csv"), row.names = FALSE)
write.csv(data.frame(prediccion = unname(pred), MSE = mse, MAE = mae, R2 = r2, R2_modelo = summary(model)$r.squared,
                     niveles_condicion = nlevels(datos$condición), niveles_recamaras = nlevels(datos$recamaras),
                     ficticias = sum(grepl("^condición|^recamaras", names(coef(modelo))))),
          file.path(base, "multiple_R.csv"), row.names = FALSE)
