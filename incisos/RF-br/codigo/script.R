# =============================================================================
# BOSQUES ALEATORIOS (OD/AM R.pdf p.54-55)
# p.54: muestreo con reemplazo, un arbol por muestra con un subconjunto aleatorio de variables en
#       cada nodo; en regresion la prediccion es el promedio de los arboles.
# T15: la semilla (42, p.55) fija la division y el bosque. Agregado para verificar: keep.inbag = TRUE
#      (no consume numeros aleatorios) y predict.all = TRUE.
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ARCHIVO <- "BR.csv"
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
suppressMessages(library(randomForest))

df <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE)

# ---- p.55, tal cual (read.csv en lugar de file.choose())
X <- df[, !(colnames(df) %in% 'precio')]
y <- df$precio
set.seed(42) # For reproducibility
train_indices <- sample(nrow(df), 0.8 * nrow(df))
X_train <- X[train_indices, ]
X_test <- X[-train_indices, ]
y_train <- y[train_indices]
y_test <- y[-train_indices]
model <- randomForest(x = X_train, y = y_train, ntree = 100, importance = TRUE, keep.inbag = TRUE) # Start with 100 trees
y_pred <- predict(model, newdata = X_test)
rmse <- sqrt(mean((y_test - y_pred)^2))
mae <- mean(abs(y_test - y_pred))
r_squared <- 1 - sum((y_test - y_pred)^2) / sum((y_test - mean(y_test))^2)
cat("\nPerformance Measures:\n")
cat("RMSE:", rmse, "\n")
cat("MAE:", mae, "\n")
cat("R-squared:", r_squared, "\n\n")
print(model)
print(importance(model))
pdf(file.path(base, "varImpPlot.pdf")); varImpPlot(model); invisible(dev.off())

# ---- Reproducibilidad: misma semilla, mismo resultado
set.seed(42)
ti2 <- sample(nrow(df), 0.8 * nrow(df))
m2 <- randomForest(x = X[ti2, ], y = y[ti2], ntree = 100, importance = TRUE, keep.inbag = TRUE)
cat("Misma semilla, mismas predicciones:", identical(unname(predict(m2, X_test)), unname(y_pred)), "\n")

# ---- Exportes para la verificacion
ind <- predict(model, newdata = X_test, predict.all = TRUE)$individual
write.csv(data.frame(fila = train_indices), file.path(base, "train_index_R.csv"), row.names = FALSE)
ind17 <- as.data.frame(apply(ind, 2, function(v) sprintf("%.17g", v))); colnames(ind17) <- paste0("arbol", seq_len(ncol(ind)))
write.csv(data.frame(fila = setdiff(seq_len(nrow(df)), train_indices), y = y_test, y_pred = sprintf("%.17g", unname(y_pred)), ind17),
          file.path(base, "predicciones_R.csv"), row.names = FALSE)
write.csv(model$inbag, file.path(base, "inbag_R.csv"), row.names = FALSE)
# T26: read.csv de R lee algunos decimales de 17 cifras a 1 ulp del redondeo correcto
# ("432.81600000000003" -> 432.81599999999997); el oraculo usa los mismos doubles que R.
write.csv(as.data.frame(lapply(X, function(v) sprintf("%.17g", v)), check.names = FALSE), file.path(base, "X_R.csv"), row.names = FALSE)
arboles <- do.call(rbind, lapply(1:model$ntree, function(k) {
  t <- getTree(model, k, labelVar = FALSE); data.frame(arbol = k, nodo = seq_len(nrow(t)), t, check.names = FALSE) }))
# write.csv escribe 15 cifras; BR tiene valores que difieren en 1e-13 (682.752 y 682.7520000000001)
# y el corte cae entre ellos, asi que cortes y predicciones van con 17 cifras.
arboles[["split point"]] <- sprintf("%.17g", arboles[["split point"]])
arboles[["prediction"]] <- sprintf("%.17g", arboles[["prediction"]])
write.csv(arboles, file.path(base, "arboles_R.csv"), row.names = FALSE)
im <- importance(model)
write.csv(data.frame(variable = rownames(im), IncMSE = im[, 1], IncNodePurity = im[, 2]), file.path(base, "importancia_R.csv"), row.names = FALSE)
write.csv(data.frame(RMSE = rmse, MAE = mae, R2 = r_squared, mtry = model$mtry, ntree = model$ntree,
                     reproducible = identical(unname(predict(m2, X_test)), unname(y_pred)),
                     variables = paste(colnames(X), collapse = "|")), file.path(base, "resumen_R.csv"), row.names = FALSE)
