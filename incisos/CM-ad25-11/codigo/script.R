# =============================================================================
# MATRIZ DE CONFUSION (OD/AM R.pdf p.49-50)
# p.49: tp, fn, fp, tn; la clase real va en las filas.
# T24: p.50 llama confusionMatrix(table(real, prediccion)), pero caret lee las FILAS como
#      prediccion. La exactitud no cambia; Sensitivity y Pos Pred Value salen intercambiadas
#      (recall <-> precision). Se imprimen las dos llamadas y se entrega confusionMatrix(pred, real).
# ORIGEN: "knn_p48" reproduce OD/AM R.pdf p.48 con OD/BR (2).csv y usa sus predicciones;
#         "csv" lee datos/clases.csv con columnas real y pred;
#         "tabla" arma la tabla 2x2 con TP, FN, FP, TN (casos de articulos).
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ORIGEN   <- "tabla"
ARCHIVO  <- "BR.csv"
POSITIVA <- "positivo"
TABLA    <- c(TP = 45, FN = 12, FP = 0, TN = 26)   # solo para ORIGEN = "tabla"
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
suppressMessages({library(caret); library(class); library(dplyr)})

if (ORIGEN == "knn_p48") {
  # ---- p.48, tal cual (con read.csv del archivo en lugar de file.choose())
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
  test_data$Prediccion <- predictions
  real <- test_data$categoria_precio; pred <- as.character(test_data$Prediccion)
  write.csv(data.frame(fila = setdiff(seq_len(nrow(df)), train_index), real = real, pred = pred),
            file.path(base, "datos", "clases.csv"), row.names = FALSE)
} else if (ORIGEN == "csv") {
  cl <- read.csv(file.path(base, "datos", "clases.csv"))
  real <- cl$real; pred <- cl$pred
}

if (ORIGEN == "tabla") {
  neg <- "negativo"
  t_rp <- as.table(matrix(c(TABLA["TP"], TABLA["FP"], TABLA["FN"], TABLA["TN"]), 2,
                          dimnames = list(real = c(POSITIVA, neg), pred = c(POSITIVA, neg))))
} else {
  niv <- sort(unique(c(real, pred)))
  neg <- setdiff(niv, POSITIVA)
  real <- factor(real, levels = c(POSITIVA, neg)); pred <- factor(pred, levels = c(POSITIVA, neg))
  t_rp <- table(real, pred)
}

# ---- p.50 literal: table(real, prediccion) -> caret la lee como (prediccion, real)  (T24)
cm <- confusionMatrix(t_rp, positive = POSITIVA)
print("Matriz de Confusión:")
print(cm$table)
print("\nOtras Métricas:")
print(cm$byClass)
accuracy <- sum(diag(cm$table)) / sum(cm$table)
print(paste("\nAccuracy:", accuracy))

# ---- Orientacion de caret (filas = prediccion): la transpuesta
cm_ok <- confusionMatrix(t(t_rp), positive = POSITIVA)
print("Matriz de Confusión (caret: filas = predicción, columnas = real):")
print(cm_ok$table)
print(cm_ok$byClass)

m <- function(c) c(Accuracy = unname(c$overall["Accuracy"]), Kappa = unname(c$overall["Kappa"]),
                   Sensitivity = unname(c$byClass["Sensitivity"]), Specificity = unname(c$byClass["Specificity"]),
                   PPV = unname(c$byClass["Pos Pred Value"]), NPV = unname(c$byClass["Neg Pred Value"]),
                   Precision = unname(c$byClass["Precision"]), Recall = unname(c$byClass["Recall"]),
                   F1 = unname(c$byClass["F1"]))
write.csv(data.frame(metrica = names(m(cm)), literal_p50 = m(cm), correcta = m(cm_ok)),
          file.path(base, "metricas_R.csv"), row.names = FALSE)
write.csv(data.frame(real = rep(rownames(t_rp), 2), pred = rep(colnames(t_rp), each = 2), n = as.vector(t_rp)),
          file.path(base, "tabla_R.csv"), row.names = FALSE)
