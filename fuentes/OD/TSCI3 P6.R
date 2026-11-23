library(cluster)
library(factoextra)
library(tidyverse)

datos <- read.csv(file.choose(), header = TRUE)
datos_norm <- scale(datos)


grafica_sil_km <- fviz_nbclust(
  datos_norm, kmeans, method = "silhouette", k.max = 10, nstart = 25
)

k_sil_km <- as.integer(as.character(grafica_sil_km$data$clusters))[
  which.max(grafica_sil_km$data$y)
]

print(grafica_sil_km +
        labs(title = "Número óptimo de clusters (K-means - Silueta)"))

grafica_wss_km <- fviz_nbclust(
  datos_norm, kmeans, method = "wss", k.max = 10, nstart = 25
)

wss_km <- grafica_wss_km$data$y
x <- seq(0, 1, length.out = length(wss_km))
y <- (wss_km - min(wss_km)) / (max(wss_km) - min(wss_km))
k_wss_km <- as.integer(as.character(grafica_wss_km$data$clusters))[which.max(abs(x + y - 1))]

print(grafica_wss_km +
        geom_vline(xintercept = k_wss_km,
                   linetype = "dashed", color = "blue") +
        labs(title = "Número óptimo de clusters (K-means - WSS)"))

gap_km <- clusGap(
  datos_norm, FUNcluster = kmeans, nstart = 25,
  K.max = 30, B = 50
)

k_gap_km <- maxSE(
  gap_km$Tab[, "gap"], gap_km$Tab[, "SE.sim"],
  method = "Tibs2001SEmax"
)

print(fviz_gap_stat(
  gap_km, maxSE = list(method = "Tibs2001SEmax", SE.factor = 1)
) + labs(title = "Número óptimo de clusters (K-means - Gap)"))

print(data.frame(
  Algoritmo = "K-means",
  Criterio = c("WSS", "Silueta", "Gap"),
  K = c(k_wss_km, k_sil_km, k_gap_km)
), row.names = FALSE)

k_km <- k_sil_km

km_res <- kmeans(datos_norm, centers = k_km, nstart = 25)

grafica_km <- fviz_cluster(
  km_res, data = datos_norm,
  ellipse.type = "convex", palette = "jco",
  ggtheme = theme_minimal()
) + labs(title = paste("K-means con k =", k_km))

print(grafica_km)

grafica_sil_pam <- fviz_nbclust(
  datos_norm, pam, method = "silhouette", k.max = 10
)

k_sil_pam <- as.integer(as.character(grafica_sil_pam$data$clusters))[
  which.max(grafica_sil_pam$data$y)
]

print(grafica_sil_pam +
        labs(title = "Número óptimo de clusters (PAM - Silueta)"))

grafica_wss_pam <- fviz_nbclust(
  datos_norm, pam, method = "wss", k.max = 10
)

wss_pam <- grafica_wss_pam$data$y
x <- seq(0, 1, length.out = length(wss_pam))
y <- (wss_pam - min(wss_pam)) / (max(wss_pam) - min(wss_pam))
k_wss_pam <- as.integer(as.character(grafica_wss_pam$data$clusters))[which.max(abs(x + y - 1))]

print(grafica_wss_pam +
        geom_vline(xintercept = k_wss_pam,
                   linetype = "dashed", color = "blue") +
        labs(title = "Número óptimo de clusters (PAM - WSS)"))

gap_pam <- clusGap(
  datos_norm, FUNcluster = function(x, k) {
    resultado <- pam(x, k = k)
    list(cluster = resultado$clustering)
  },
  K.max = 10, B = 50
)

k_gap_pam <- maxSE(
  gap_pam$Tab[, "gap"], gap_pam$Tab[, "SE.sim"],
  method = "Tibs2001SEmax"
)

print(fviz_gap_stat(
  gap_pam, maxSE = list(method = "Tibs2001SEmax", SE.factor = 1)
) + labs(title = "Número óptimo de clusters (PAM - Gap)"))

print(data.frame(
  Algoritmo = "PAM",
  Criterio = c("WSS", "Silueta", "Gap"),
  K = c(k_wss_pam, k_sil_pam, k_gap_pam)
), row.names = FALSE)

k_pam <- k_sil_pam

pam_res <- pam(datos_norm, k = k_pam)

grafica_pam <- fviz_cluster(
  pam_res, data = datos_norm,
  ellipse.type = "t", palette = "jco",
  ggtheme = theme_minimal()
) + labs(title = paste("PAM con k =", k_pam))

print(grafica_pam)

grafica_sil_clara <- fviz_nbclust(
  datos_norm, clara, method = "silhouette", k.max = 10, samples = 50, pamLike = TRUE
)

k_sil_clara <- as.integer(as.character(grafica_sil_clara$data$clusters))[
  which.max(grafica_sil_clara$data$y)
]

print(grafica_sil_clara +
        labs(title = "Número óptimo de clusters (CLARA - Silueta)"))

grafica_wss_clara <- fviz_nbclust(
  datos_norm, clara, method = "wss", k.max = 10, samples = 50, pamLike = TRUE
)

wss_clara <- grafica_wss_clara$data$y
x <- seq(0, 1, length.out = length(wss_clara))
y <- (wss_clara - min(wss_clara)) / (max(wss_clara) - min(wss_clara))
k_wss_clara <- as.integer(as.character(grafica_wss_clara$data$clusters))[which.max(abs(x + y - 1))]

print(grafica_wss_clara +
        geom_vline(xintercept = k_wss_clara,
                   linetype = "dashed", color = "blue") +
        labs(title = "Número óptimo de clusters (CLARA - WSS)"))

gap_clara <- clusGap(
  datos_norm, FUNcluster = function(x, k) {
    resultado <- clara(x, k = k, samples = 50, pamLike = TRUE)
    list(cluster = resultado$clustering)
  },
  K.max = 10, B = 50
)

k_gap_clara <- maxSE(
  gap_clara$Tab[, "gap"], gap_clara$Tab[, "SE.sim"],
  method = "Tibs2001SEmax"
)

print(fviz_gap_stat(
  gap_clara, maxSE = list(method = "Tibs2001SEmax", SE.factor = 1)
) + labs(title = "Número óptimo de clusters (CLARA - Gap)"))

print(data.frame(
  Algoritmo = "CLARA",
  Criterio = c("WSS", "Silueta", "Gap"),
  K = c(k_wss_clara, k_sil_clara, k_gap_clara)
), row.names = FALSE)

k_clara <- k_sil_clara

clara_res <- clara(datos_norm, k = k_clara, samples = 50, pamLike = TRUE)

grafica_clara <- fviz_cluster(
  clara_res, data = datos_norm,
  ellipse.type = "norm", palette = "jco",
  ggtheme = theme_minimal()
) + labs(title = paste("CLARA con k =", k_clara))

print(grafica_clara)

print(data.frame(
  Algoritmo = c("K-means", "PAM", "CLARA"),
  K_WSS = c(k_wss_km, k_wss_pam, k_wss_clara),
  K_Silueta = c(k_sil_km, k_sil_pam, k_sil_clara),
  K_Gap = c(k_gap_km, k_gap_pam, k_gap_clara),
  K_Utilizada = c(k_km, k_pam, k_clara)
), row.names = FALSE)

print(ggpubr::ggarrange(
  grafica_km, grafica_pam, grafica_clara,
  ncol = 3, nrow = 1
))

datos_clasificados <- datos %>%
  mutate(Cluster_KMeans = km_res$cluster,
         Cluster_PAM = pam_res$clustering,
         Cluster_CLARA = clara_res$clustering)

head(datos_clasificados)

write.csv(datos_clasificados, "datos_clasificados_completo.csv", row.names = TRUE)
