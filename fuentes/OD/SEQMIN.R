library(arules)
library(arulesSequences)

file_path <- file.choose()
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
    support = 0.01,
    maxsize = 3,
    maxlen = 4
  ),
  control = list(
    tidLists = TRUE,
    verbose = TRUE
  )
)

df_freq <- as(freq, "data.frame")
df_freq$support <- as.numeric(df_freq$support)
df_freq <- df_freq[order(-df_freq$support), ]

head(df_freq)
