# =============================================================================
# PATRONES SECUENCIALES CON cspade (copia de OD/SEQMIN.R)
# Cambios: la ruta del archivo en lugar de file.choose(), los parametros arriba y el
# resultado completo en patrones_R.csv. El resto es el script del curso.
# Ejecutar: Rscript codigo/script.R        (desde la carpeta del problema)
# =============================================================================
ARCHIVO <- "SEQMIN.csv"
SOPORTE <- 0.01
MAXSIZE <- 3
MAXLEN  <- 4
options(width = 200)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
suppressPackageStartupMessages({
library(arules)
library(arulesSequences)
})

file_path <- file.path(base, "datos", ARCHIVO)
lines <- readLines(file_path)

parse_spmf <- function(lines) {
  res <- list()
  idx <- 1L
  
  for (sid in seq_along(lines)) {
    tokens <- scan(text = lines[sid], what = integer(), quiet = TRUE)
    if (length(tokens) == 0L) next
    
    eid <- 1L
    items_in_event <- integer(0)
    
    for (tok in tokens) {
      if (tok == -1L || tok == -2L) {
        if (length(items_in_event) > 0L) {
          res[[idx]] <- data.frame(
            sequenceID = sid,
            eventID = eid,
            item = as.character(items_in_event)
          )
          idx <- idx + 1L
          eid <- eid + 1L
          items_in_event <- integer(0)
        }
        
        if (tok == -2L) break
      } else {
        items_in_event <- c(items_in_event, tok)
      }
    }
  }
  
  do.call(rbind, res)
}

data_raw <- parse_spmf(lines)

data_raw$sequenceID <- as.integer(data_raw$sequenceID)
data_raw$eventID <- as.integer(data_raw$eventID)
data_raw$item <- as.character(data_raw$item)

eventos <- aggregate(
  item ~ sequenceID + eventID,
  data = data_raw,
  FUN = function(x) paste(unique(x), collapse = " ")
)

eventos <- eventos[
  order(eventos$sequenceID, eventos$eventID),
]

lineas_eventos <- paste(
  eventos$sequenceID,
  eventos$eventID,
  eventos$item
)

tmp_file <- tempfile(fileext = ".txt")
writeLines(lineas_eventos, tmp_file)

seq_data <- read_baskets(
  con = tmp_file,
  info = c("sequenceID", "eventID")
)

freq <- cspade(
  seq_data,
  parameter = list(
    support = SOPORTE,
    maxsize = MAXSIZE,
    maxlen = MAXLEN
  ),
  control = list(
    tidLists = TRUE,
    verbose = FALSE
  )
)

df_freq <- as(freq, "data.frame")
df_freq$support <- as.numeric(df_freq$support)
df_freq <- df_freq[order(-df_freq$support), ]

head(df_freq)
cat(sprintf("Secuencias: %d; patrones frecuentes: %d\n", length(unique(data_raw$sequenceID)), nrow(df_freq)))
write.csv(df_freq, file.path(base, "patrones_R.csv"), row.names = FALSE)
