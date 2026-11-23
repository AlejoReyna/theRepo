# =============================================================================
# K VECINOS MAS CERCANOS (OD/AM R.pdf p.43-48) Y DETERMINACION DE k (p.45-47, p.51-53)
# T5: p.48 no normaliza; se respeta. T15: class::knn y caret desempatan al azar; la semilla es la
#     de p.48 (42) y los indices de entrenamiento y los pliegues se exportan para el oraculo.
# Unico agregado a p.53: savePredictions = "all" (no consume numeros aleatorios) para verificar.
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ARCHIVO <- "BR.csv"
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
suppressMessages({library(class); library(dplyr); library(caret)})

# ---- p.48
df <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE)
median_price <- median(df$precio)
df$categoria_precio <- ifelse(df$precio >= median_price, 'alto', 'bajo')
df_selected <- df %>% select(recamaras, baños, m2_construcción, m2_terreno, pisos, condición, categoria_precio)
set.seed(42)
train_index <- sample(1:nrow(df_selected), 0.75 * nrow(df_selected))
train_data <- df_selected[train_index, ]
test_data <- df_selected[-train_index, ]
knn_model <- knn(train = train_data %>% select(-categoria_precio),
                 test = test_data %>% select(-categoria_precio),
                 cl = train_data$categoria_precio, k = 3)
predictions <- knn_model
print(head(predictions, 5))

# ---- p.50 (S15, orientacion correcta; T24)
test_data$Prediccion <- predictions
cm <- confusionMatrix(factor(test_data$Prediccion, levels = c("alto", "bajo")), factor(test_data$categoria_precio, levels = c("alto", "bajo")))
print(cm$table); print(cm$overall["Accuracy"])

# ---- p.53: k por validacion cruzada de 10 pliegues
train_data$categoria_precio <- as.factor(train_data$categoria_precio)
k_values <- seq(1, 15, by = 2)
cv_results <- train(categoria_precio ~ ., data = train_data, method = "knn",
                    tuneGrid = data.frame(k = k_values),
                    trControl = trainControl(method = "cv", number = 10, savePredictions = "all"))
best_k <- cv_results$bestTune$k
print(paste("Mejor valor de k:", best_k))
best_accuracy <- max(cv_results$results$Accuracy)
print(paste("Precisión del mejor k:", best_accuracy))
print(cv_results$results[, c("k", "Accuracy", "Kappa")])
pdf(file.path(base, "k_vs_exactitud.pdf")); plot(cv_results); invisible(dev.off())

# ---- p.45-47: k desconocido, WCSS y codo (k-means sobre las mismas columnas, semilla declarada)
X <- df_selected %>% select(-categoria_precio)
set.seed(42)
wcss <- sapply(1:10, function(k) kmeans(X, centers = k, nstart = 10)$tot.withinss)
print(data.frame(k = 1:10, WCSS = wcss))
set.seed(42)
grupos <- sapply(1:10, function(k) kmeans(X, centers = k, nstart = 10)$cluster)

# ---- Exportes para la verificacion
write.csv(data.frame(fila = train_index), file.path(base, "train_index_R.csv"), row.names = FALSE)
write.csv(data.frame(fila = setdiff(seq_len(nrow(df)), train_index), real = test_data$categoria_precio, pred = as.character(predictions)),
          file.path(base, "predicciones_R.csv"), row.names = FALSE)
pl <- cv_results$pred
write.csv(data.frame(k = pl$k, fold = pl$Resample, fila_train = pl$rowIndex, obs = pl$obs, pred = pl$pred),
          file.path(base, "cv_pred_R.csv"), row.names = FALSE)
write.csv(cv_results$results[, c("k", "Accuracy", "Kappa")], file.path(base, "cv_resultados_R.csv"), row.names = FALSE)
write.csv(data.frame(k = 1:10, WCSS = wcss), file.path(base, "wcss_R.csv"), row.names = FALSE)
write.csv(as.data.frame(grupos), file.path(base, "wcss_grupos_R.csv"), row.names = FALSE)
write.csv(data.frame(mediana = median_price, best_k = best_k, best_accuracy = best_accuracy,
                     exactitud_k3 = unname(cm$overall["Accuracy"])), file.path(base, "resumen_R.csv"), row.names = FALSE)
