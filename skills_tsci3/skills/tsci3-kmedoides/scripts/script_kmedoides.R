# =============================================================================
# K-MEDOIDES EN R
#  Parte 1: criterio de clase (DOLLY Sheet2) y PAM sobre los mismos datos min-max, con la
#           silueta de cluster::silhouette, para comparar con resolver.py
#  Parte 2: PAM y CLARA del curso (OD/TSCI3 P6.R): scale, silueta, WSS, gap y el k final
# Ejecutar: Rscript codigo/script.R        (desde la carpeta del problema)
# =============================================================================
ARCHIVO  <- "datos.csv"
COLUMNAS <- NULL
SEMILLA  <- 1851265         # T15: se fija y se declara
KMAX     <- 10
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

# ---- Parte 1: criterio de clase y PAM con min-max ----------------------------
mn <- sapply(datos, min); mx <- sapply(datos, max)
Z <- sweep(sweep(as.matrix(datos), 2, 1 / (mx - mn), "*"), 2, -mn / (mx - mn), "+")
c0 <- apply(Z, 2, min); c1 <- apply(Z, 2, max)
d0 <- sqrt(rowSums(sweep(Z, 2, c0)^2)); d1 <- sqrt(rowSums(sweep(Z, 2, c1)^2))
dmin <- pmin(d0, d1); p0 <- as.numeric(dmin == d0); p1 <- as.numeric(dmin == d1)
c0n <- (colSums(Z * p0) + c0) / (sum(p0) + 1); c1n <- (colSums(Z * p1) + c1) / (sum(p1) + 1)
e0 <- sqrt(rowSums(sweep(Z, 2, c0n)^2)); e1 <- sqrt(rowSums(sweep(Z, 2, c1n)^2))
i0 <- which.min(e0); i1 <- which.min(e1)
if (i1 == i0) i1 <- order(e1)[2]
dm0 <- sqrt(rowSums(sweep(Z, 2, Z[i0, ])^2)); dm1 <- sqrt(rowSums(sweep(Z, 2, Z[i1, ])^2))
grupo <- ifelse(dm0 <= dm1, 1, 2)
D <- dist(Z)
sil_clase <- silhouette(grupo, D)
cat(sprintf("Criterio de clase: M0 = registro %d (dist %.6f), M1 = registro %d (dist %.6f); |M0| = %d, |M1| = %d; costo = %.6f; silueta media = %.4f\n",
            i0, e0[i0], i1, e1[i1], sum(dm0 <= dm1), sum(dm1 <= dm0), sum(pmin(dm0, dm1)), mean(sil_clase[, "sil_width"])))
pam_mm <- pam(Z, k = 2)
sil_pam <- silhouette(pam_mm$clustering, D)
cat(sprintf("PAM sobre min-max: medoides = registros %s; costo = %.6f; tamanos = %s; silueta media = %.4f\n",
            paste(pam_mm$id.med, collapse = ", "), sum(pmin(as.matrix(D)[, pam_mm$id.med[1]], as.matrix(D)[, pam_mm$id.med[2]])),
            paste(pam_mm$clusinfo[, "size"], collapse = ", "), mean(sil_pam[, "sil_width"])))
write.csv(data.frame(registro = seq_len(nrow(Z)), grupo_clase = grupo, sil_clase = sil_clase[, "sil_width"],
                     grupo_pam = pam_mm$clustering, sil_pam = sil_pam[, "sil_width"]),
          file.path(base, "kmedoides_R.csv"), row.names = FALSE)
write.csv(data.frame(M0 = i0, M1 = i1, pam_medoide_1 = pam_mm$id.med[1], pam_medoide_2 = pam_mm$id.med[2]),
          file.path(base, "medoides_R.csv"), row.names = FALSE)

# ---- Parte 2: P6.R (PAM y CLARA) -----------------------------------------------
set.seed(SEMILLA)
datos_norm <- scale(datos)
sel <- if (nrow(datos_norm) > MUESTRA) sample(nrow(datos_norm), MUESTRA) else seq_len(nrow(datos_norm))
dn <- datos_norm[sel, , drop = FALSE]
elegir <- function(fun, nombre, ...) {
  g_sil <- fviz_nbclust(dn, fun, method = "silhouette", k.max = KMAX, ...)
  k_sil <- as.integer(as.character(g_sil$data$clusters))[which.max(g_sil$data$y)]
  ggsave(file.path(base, sprintf("%s_silueta.png", tolower(nombre))), g_sil + labs(title = sprintf("Número óptimo de clusters (%s - Silueta)", nombre)), width = 7, height = 4.5)
  g_wss <- fviz_nbclust(dn, fun, method = "wss", k.max = KMAX, ...)
  w <- g_wss$data$y; x <- seq(0, 1, length.out = length(w)); y <- (w - min(w)) / (max(w) - min(w))
  k_wss <- as.integer(as.character(g_wss$data$clusters))[which.max(abs(x + y - 1))]
  ggsave(file.path(base, sprintf("%s_wss.png", tolower(nombre))), g_wss + geom_vline(xintercept = k_wss, linetype = "dashed", color = "blue") +
           labs(title = sprintf("Número óptimo de clusters (%s - WSS)", nombre)), width = 7, height = 4.5)
  gap <- clusGap(dn, FUNcluster = function(x, k) list(cluster = fun(x, k = k, ...)$clustering), K.max = min(KMAX, nrow(dn) - 1), B = 50, verbose = FALSE)
  k_gap <- maxSE(gap$Tab[, "gap"], gap$Tab[, "SE.sim"], method = "Tibs2001SEmax")
  ggsave(file.path(base, sprintf("%s_gap.png", tolower(nombre))), fviz_gap_stat(gap, maxSE = list(method = "Tibs2001SEmax", SE.factor = 1)) +
           labs(title = sprintf("Número óptimo de clusters (%s - Gap)", nombre)), width = 7, height = 4.5)
  data.frame(Algoritmo = nombre, Criterio = c("WSS", "Silueta", "Gap"), K = c(k_wss, k_sil, k_gap))
}
t_pam <- elegir(pam, "PAM")
t_clara <- elegir(clara, "CLARA", samples = 50, pamLike = TRUE)
tabla_k <- rbind(t_pam, t_clara); print(tabla_k, row.names = FALSE)
write.csv(tabla_k, file.path(base, "kmedoides_k_R.csv"), row.names = FALSE)
k_pam <- t_pam$K[t_pam$Criterio == "Silueta"]; k_clara <- t_clara$K[t_clara$Criterio == "Silueta"]
pam_res <- pam(datos_norm, k = k_pam)
clara_res <- clara(datos_norm, k = k_clara, samples = 50, pamLike = TRUE)
cat(sprintf("\nPAM con k = %d: medoides (registros) %s, tamanos %s, silueta media %.4f\n", k_pam,
            paste(pam_res$id.med, collapse = ", "), paste(pam_res$clusinfo[, "size"], collapse = ", "), pam_res$silinfo$avg.width))
cat(sprintf("CLARA con k = %d: medoides (registros) %s, tamanos %s\n", k_clara,
            paste(clara_res$i.med, collapse = ", "), paste(clara_res$clusinfo[, "size"], collapse = ", ")))
ggsave(file.path(base, "pam_clusters.png"), fviz_cluster(pam_res, data = datos_norm, ellipse.type = "t", palette = "jco",
       ggtheme = theme_minimal()) + labs(title = paste("PAM con k =", k_pam)), width = 7, height = 5)
ggsave(file.path(base, "clara_clusters.png"), fviz_cluster(clara_res, data = datos_norm, ellipse.type = "norm", palette = "jco",
       ggtheme = theme_minimal()) + labs(title = paste("CLARA con k =", k_clara)), width = 7, height = 5)
datos_clasificados <- datos %>% mutate(Cluster_PAM = pam_res$clustering, Cluster_CLARA = clara_res$clustering)
write.csv(datos_clasificados, file.path(base, "kmedoides_resultado_R.csv"), row.names = TRUE)
