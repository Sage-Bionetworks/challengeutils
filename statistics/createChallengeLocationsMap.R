library("ggmap")
library(maptools)
library(maps)


makeChallengeLocationMap() <- function(location_text_filePath, mapName)
  visited = read.csv(location_text_filePath,sep="\t",stringsAsFactors = F)
  ll.visited <- geocode(visited$locations)
  ll.visited$combined <- paste(ll.visited$lon, ll.visited$lat)
  noduplicates <- ll.visited[!duplicated(ll.visited$combined),]
  count <- table(ll.visited$combined)
  noduplicates$density <- count[match(noduplicates$combined, names(count))]
  visit.x <- noduplicates$lon
  visit.y <- noduplicates$lat
  pdf(mapName)
  map("world", fill=TRUE, col="grey", bg="white", ylim=c(-60, 90), mar=c(0,0,0,0))
  #log10 is 0 sometimes
  points(visit.x,visit.y, col="red", pch=20, bg=24, cex=log10(noduplicates$density)*2+1, lwd=.4)
  dev.off()

#Must make challenge_locations.txt first (These functions can be found in DREAMchallenge_analysis.py)
location_text_filePath <- "~/sage_projects/DREAM/statistics/challenge_locations.txt"
makeChallengeLocationMap(location_text_filePath, "~/sage_projects/DREAM/statistics/all_challenge_locations.pdf")

location_text_filePath <- "~/sage_projects/DREAM/statistics/DM_challenge_locations.txt"
makeChallengeLocationMap(location_text_filePath, "~/sage_projects/DREAM/statistics/DM_challenge_locations.pdf")