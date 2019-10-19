library(data.table)
library(ggplot2)
library("ggmap")
library(maptools)
library(maps)
library(synapser)
library(glue)
library(ggrepel)


synLogin()

### BEFORE RUNNING THESE FUNCTIONS MAKE SURE YOU RUN: python createChallengeStatDf.py
### TO GENERATE THIS FILE: challenge_stats.tsv
create_participation_plot <- function(challengestat_filepath, pdfPath, orderByYear=T) {
  challenge_stats = read.csv(challengestat_filepath, sep = "\t")
  year = as.character(challenge_stats$year)
  participants = data.frame(year)
  participants$number = challenge_stats$number_participants
  participants$name = challenge_stats$challenges
  if (orderByYear) {
    participants = participants[order(participants$year, participants$number, decreasing = T),]
  } else{
    participants = participants[order(participants$number,decreasing = T),]
  }
  participants$indexing = seq_along(participants$year)
  
  ggplot(participants,
         aes(x = reorder(name,-indexing),
             y = number,
             fill = year)) + 
    geom_bar(stat = "identity") + coord_flip() +
    ylab("Number of Participants") + theme_bw() +
    theme(#panel.background = element_blank(),
          axis.text.y = element_text(size = 14),
          axis.title.y = element_blank(),
          axis.text.x  = element_text(size = 14),
          title = element_text(size = 14),
          legend.text = element_text(size = 14),
          legend.justification = c(1,0), 
          legend.position = c(1,0),
          plot.margin = margin(20, 20, 20, 20)) + 
    scale_fill_brewer(palette = "Set1")
  ggsave(pdfPath, width = 17, height = 10)
}
challengeStatDfPath = "statistics/challenge_stats.tsv"
pdfPath = "statistics/challenge_participation_ordered.pdf"
create_participation_plot(challengeStatDfPath, pdfPath, orderByYear = T)
pdfPath = "statistics/challenge_participation.pdf"
create_participation_plot(challengeStatDfPath, pdfPath, orderByYear = F)

# draw a map in R from lat/long
# https://gist.github.com/kdaily/77993a19a90cc0d34c4b5799230f854f
# map to users and aggregate to country or other level
# https://gist.github.com/kdaily/c68fe3038780057db530891d2603393d

synapse_location_df <- function(ur) {
  resp <- httr::GET(url)
  data_raw_ugly <- jsonlite::fromJSON(rawToChar(resp$content))
  locations_df <- tibble::tibble(location = data_raw_ugly$location,
                                 longitude = purrr::map_dbl(data_raw_ugly$latLng, 2),
                                 latitude = purrr::map_dbl(data_raw_ugly$latLng, 1))
  
  return(locations_df)
}

### CREATE CHALLENGE LOCATION MAPS
makeChallengeLocationMap <- function(mapName) {
  
  challenge_teams = synTableQuery("select challengeParticipants, challengePreregistrants from syn10163902")
  challenge_teamsdf = as.data.frame(challenge_teams)
  all_teams = c(challenge_teamsdf$challengeParticipants, challenge_teamsdf$challengePreregistrants)
  all_teams = all_teams[!is.na(all_teams)]
  all_locationsdf = data.frame()
  for (team in all_teams) {
    url = glue::glue("https://s3.amazonaws.com/geoloc.sagebase.org/{team}.json")
    locationdf = synapse_location_df(url)
    all_locationsdf = rbind(all_locationsdf, locationdf)
  }
  
  
  all_locationsdf$combined <- paste(all_locationsdf$longitude, all_locationsdf$latitude)
  noduplicates <- all_locationsdf[!duplicated(all_locationsdf$combined),]
  count <- table(all_locationsdf$combined)
  noduplicates$density <- count[match(noduplicates$combined, names(count))]
  visit.x <- noduplicates$longitude
  visit.y <- noduplicates$latitude
  pdf("locations_density_huge.pdf")
  pdf(mapName)
  # mapgilbert <- get_map(maptype = c("satellite")
  maps::map("world",
      fill = TRUE,
      col = "grey",
      bg = "white",
      ylim = c(-60, 90),
      mar = c(0,0,0,0))
  #log10 is 0 sometimes
  points(visit.x,visit.y,
         col="red",
         pch=20,
         bg=24,
         cex=log10(noduplicates$density)*2 + 1, lwd=.4)
  points(visit.x,visit.y,
         col = "red",
         pch = 20,
         bg = 24,
         lwd = .4)
  dev.off()
  # pdf("usa.pdf")
  # map("usa",
  #     fill = TRUE,
  #     col = "grey",
  #     bg = "white",
  #     mar = c(0,0,0,0))
  # #log10 is 0 sometimes
  # points(visit.x,
  #        visit.y,
  #        col = "red",
  #        pch = 20,
  #        bg = 24,
  #        cex = log10(noduplicates$density)*3 + 1,
  #        lwd = .4)
  # dev.off()
  # pdf("europe.pdf")
  # map("world",
  #     fill = TRUE,
  #     col = "grey",
  #     bg = "white",
  #     xlim = c(-20, 59),
  #     ylim = c(35, 71),
  #     mar = c(0,0,0,0))
  # points(visit.x,
  #        visit.y,
  #        col = "red",
  #        pch = 20,
  #        bg = 24,
  #        cex = log10(noduplicates$density)*3 + 1,
  #        lwd = .4)
  # dev.off()
  # pdf("china.pdf")
  # map("world",
  #     fill = TRUE,
  #     col = "grey",
  #     bg = "white",
  #     xlim = c(50, 129),
  #     ylim = c(15, 51),
  #     mar = c(0,0,0,0))
  # points(visit.x,
  #        visit.y,
  #        col = "red",
  #        pch = 20,
  #        bg = 24,
  #        cex = log10(noduplicates$density)*3 + 1,
  #        lwd = .4)
  # dev.off()
}

#Must make challenge_stats.tsv exist first (This file can be generated by running python createChallengeStatDf.py)
makeChallengeLocationMap("statistics/challenge_locations.pdf")

#location_text_filePath <- "~/sage_projects/DREAM/statistics/DM_challenge_locations.txt"
#makeChallengeLocationMap(location_text_filePath, "~/sage_projects/DREAM/statistics/DM_challenge_locations.pdf")




