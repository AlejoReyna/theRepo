# =============================================================================
# K-MEANS EN R
#  Parte 1: el ejercicio de clase en R (min-max, centroides min/max, C' = (sum + C)/(n + 1))
#  Parte 2: la seleccion de k y el k-means del curso (OD/TSCI3 P6.R): scale, silueta,
#           WSS (codo = max |x + y - 1|), gap (Tibs2001SEmax) y kmeans(nstart = 25)
# Ejecutar: Rscript codigo/script.R        (desde la carpeta del problema)
# =============================================================================
ARCHIVO  <- "mochila_.csv"
COLUMNAS <- c("Peso", "Volumen", "Beneficio")
SEMILLA  <- 1851265         # T15: P6.R no fija semilla; aqui se fija y se declara
KMAX     <- 10              # fviz_nbclust (P6.R)
KMAX_GAP <- 30              # clusGap (P6.R)
MUESTRA  <- 3000            # T21: con mas filas, la seleccion de k usa una muestra

suppressPackageStartupMessages({ library(cluster); library(factoextra); library(tidyverse) })
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()

datos <- read.csv(file.path(base, "datos", ARCHIVO), header = TRUE, check.names = FALSE)
if (!is.null(COLUMNAS)) datos <- datos[, COLUMNAS]
datos[] <- lapply(datos, function(x) as.numeric(gsub(",", "", as.character(x))))
datos <- datos[complete.cases(datos), ]
cat(sprintf("Registros: %d   Variables: %s\n", nrow(datos), paste(names(datos), collapse = ", ")))

# ---- Parte 1: ejercicio de clase --------------------------------------------
mn <- sapply(datos, min); mx <- sapply(datos, max)
m <- 1 / (mx - mn); b <- -m * mn
Z <- sweep(sweep(as.matrix(datos), 2, m, "*"), 2, b, "+")          # y = m*x + b
c0 <- apply(Z, 2, min); c1 <- apply(Z, 2, max)
clase <- list(); anterior <- NULL
for (it in 1:100) {
  d0 <- sqrt(rowSums(sweep(Z, 2, c0)^2)); d1 <- sqrt(rowSums(sweep(Z, 2, c1)^2))
  dmin <- pmin(d0, d1)
  p0 <- as.numeric(dmin == d0); p1 <- as.numeric(dmin == d1)
  n0 <- sum(p0); n1 <- sum(p1)
  nc0 <- (colSums(Z * p0) + c0) / (n0 + 1); nc1 <- (colSums(Z * p1) + c1) / (n1 + 1)
  pert <- ifelse(p0 == 1 & p1 == 1, 2, ifelse(p0 == 1, 0, 1))
  cambios <- if (is.null(anterior)) NA else sum(pert != anterior)
  clase[[it]] <- data.frame(iteracion = it, n0 = n0, n1 = n1, empates = sum(pert == 2),
                            suma_dmin = sum(dmin), cambios = cambios,
                            t(setNames(c0, paste0("C0_", seq_along(c0)))), t(setNames(c1, paste0("C1_", seq_along(c1)))))
  cat(sprintf("Iteracion %d: |C0| = %d, |C1| = %d, suma DMIN = %.6f, cambios = %s\n", it, n0, n1, sum(dmin),
              ifelse(is.na(cambios), "-", cambios)))
  if (!is.na(cambios) && cambios == 0) break
  anterior <- pert; c0 <- nc0; c1 <- nc1
}
clase <- do.call(rbind, clase)
write.csv(clase, file.path(base, "kmeans_clase_R.csv"), row.names = FALSE)

# ---- Parte 2: P6.R ------------------------------------------------------------
set.seed(SEMILLA)
datos_norm <- scale(datos)
sel <- if (nrow(datos_norm) > MUESTRA) sample(nrow(datos_norm), MUESTRA) else seq_len(nrow(datos_norm))
if (length(sel) < nrow(datos_norm)) cat(sprintf("Seleccion de k con una muestra de %d filas (T21)\n", length(sel)))
dn <- datos_norm[sel, , drop = FALSE]

grafica_sil_km <- fviz_nbclust(dn, kmeans, method = "silhouette", k.max = KMAX, nstart = 25)
k_sil_km <- as.integer(as.character(grafica_sil_km$data$clusters))[which.max(grafica_sil_km$data$y)]
ggsave(file.path(base, "kmeans_silueta.png"), grafica_sil_km + labs(title = "Número óptimo de clusters (K-means - Silueta)"), width = 7, height = 4.5)

grafica_wss_km <- fviz_nbclust(dn, kmeans, method = "wss", k.max = KMAX, nstart = 25)
wss_km <- grafica_wss_km$data$y
x <- seq(0, 1, length.out = length(wss_km))
y <- (wss_km - min(wss_km)) / (max(wss_km) - min(wss_km))
k_wss_km <- as.integer(as.character(grafica_wss_km$data$clusters))[which.max(abs(x + y - 1))]
ggsave(file.path(base, "kmeans_wss.png"), grafica_wss_km + geom_vline(xintercept = k_wss_km, linetype = "dashed", color = "blue") +
         labs(title = "Número óptimo de clusters (K-means - WSS)"), width = 7, height = 4.5)

gap_km <- clusGap(dn, FUNcluster = kmeans, nstart = 25, K.max = min(KMAX_GAP, nrow(dn) - 1), B = 50, verbose = FALSE)
k_gap_km <- maxSE(gap_km$Tab[, "gap"], gap_km$Tab[, "SE.sim"], method = "Tibs2001SEmax")
ggsave(file.path(base, "kmeans_gap.png"), fviz_gap_stat(gap_km, maxSE = list(method = "Tibs2001SEmax", SE.factor = 1)) +
         labs(title = "Número óptimo de clusters (K-means - Gap)"), width = 7, height = 4.5)

tabla_k <- data.frame(Algoritmo = "K-means", Criterio = c("WSS", "Silueta", "Gap"), K = c(k_wss_km, k_sil_km, k_gap_km))
print(tabla_k, row.names = FALSE)
write.csv(tabla_k, file.path(base, "kmeans_k_R.csv"), row.names = FALSE)

k_km <- k_sil_km                                   # P6.R: el k final es el de la silueta
km_res <- kmeans(datos_norm, centers = k_km, nstart = 25)
cat(sprintf("\nkmeans con k = %d: tamanos %s; WSS total = %.4f; BSS/TSS = %.4f\n", k_km,
            paste(km_res$size, collapse = ", "), km_res$tot.withinss, km_res$betweenss / km_res$totss))
print(round(km_res$centers, 4))
grafica_km <- fviz_cluster(km_res, data = datos_norm, ellipse.type = "convex", palette = "jco",
                           ggtheme = theme_minimal()) + labs(title = paste("K-means con k =", k_km))
ggsave(file.path(base, "kmeans_clusters.png"), grafica_km, width = 7, height = 5)
write.csv(data.frame(datos, cluster = km_res$cluster), file.path(base, "kmeans_resultado_R.csv"), row.names = FALSE)
