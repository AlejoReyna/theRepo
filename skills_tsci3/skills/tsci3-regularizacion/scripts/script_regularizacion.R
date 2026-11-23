# =============================================================================
# REGRESION LASSO Y RIDGE (OD/AM R.pdf p.29-32)
# p.30: alpha = 1 para Lasso. p.32 programa Ridge con alpha <- 1.0 (T3): con glmnet eso es Lasso
#       otra vez. Se calculan las dos lecturas: la literal (alpha = 1) y Ridge (alpha = 0), que es
#       la que cumple p.31 (encoge sin anular coeficientes).
# T15: cv.glmnet reparte los pliegues al azar; la semilla se fija y se declara.
# Ejecutar: Rscript codigo/script.R
# =============================================================================
ARCHIVO <- "BR.csv"
SEMILLA <- 1851265
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
options(width = 200, digits = 10)
suppressMessages(library(glmnet))

datos <- read.csv(file.path(base, "datos", ARCHIVO), check.names = FALSE)

# ---- p.30: Lasso
x <- model.matrix(precio ~ ., data = datos)[, -1]
y <- datos$precio                                   # Variable respuesta
modelo_lasso <- glmnet(x, y, alpha = 1)             # alpha = 1 para Lasso
set.seed(SEMILLA)
cv_lasso <- cv.glmnet(x, y, alpha = 1)
mejor_lambda <- cv_lasso$lambda.min
coeficientes <- coef(modelo_lasso, s = mejor_lambda)
print(coeficientes)
prediccionesl <- predict(modelo_lasso, newx = x, s = mejor_lambda)
mse <- mean((datos$precio - prediccionesl)^2)
print(paste("MSE:", mse))

# ---- p.32: Ridge, lectura literal (alpha <- 1.0) y lectura de p.31 (alpha = 0)
X_matrix <- model.matrix(precio ~ ., data = datos)[, -1]
ridge <- function(alpha, etiqueta) {
  ridge_model <- glmnet(X_matrix, datos$precio, alpha = alpha)
  set.seed(SEMILLA)
  cv_fit <- cv.glmnet(X_matrix, datos$precio, alpha = alpha)
  best_lambda <- cv_fit$lambda.min
  cat("\n==== Ridge,", etiqueta, ": alpha =", alpha, " best_lambda =", best_lambda, "\n")
  print(coef(ridge_model, s = best_lambda))
  predicciones <- predict(ridge_model, newx = X_matrix, s = best_lambda)
  mse <- mean((datos$precio - predicciones)^2)
  print(paste("MSE:", mse))
  list(modelo = ridge_model, lambda = best_lambda, pred = as.numeric(predicciones), mse = mse)
}
r_lit <- ridge(1.0, "literal p.32 (T3)")
r_0 <- ridge(0, "p.31")

# ---- Exportes para la verificacion
cf <- function(m, s) { v <- as.matrix(coef(m, s = s)); data.frame(termino = rownames(v), coef = v[, 1]) }
L <- cf(modelo_lasso, mejor_lambda); R1 <- cf(r_lit$modelo, r_lit$lambda); R0 <- cf(r_0$modelo, r_0$lambda)
write.csv(data.frame(termino = L$termino, lasso = L$coef, ridge_literal = R1$coef, ridge_alpha0 = R0$coef),
          file.path(base, "coef_R.csv"), row.names = FALSE)
write.csv(data.frame(y = y, lasso = as.numeric(prediccionesl), ridge_literal = r_lit$pred, ridge_alpha0 = r_0$pred),
          file.path(base, "predicciones_R.csv"), row.names = FALSE)
write.csv(data.frame(modelo = c("lasso", "ridge_literal", "ridge_alpha0"), alpha = c(1, 1, 0),
                     lambda_min = c(mejor_lambda, r_lit$lambda, r_0$lambda),
                     MSE = c(mse, r_lit$mse, r_0$mse),
                     ceros = c(sum(L$coef[-1] == 0), sum(R1$coef[-1] == 0), sum(R0$coef[-1] == 0))),
          file.path(base, "resumen_R.csv"), row.names = FALSE)
