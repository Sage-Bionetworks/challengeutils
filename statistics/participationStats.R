library(synapseClient)
synapseLogin()

getSubmissionCount = function(evalId, status) {
  LIMIT = 10
  OFFSET = 0
  subs = synGetSubmissions(evalId,status = status)
  challenge_stats = list()
  while (OFFSET < subs@totalNumberOfResults) {
    subs = synGetSubmissions(evalId,status = status, limit=LIMIT, offset = OFFSET)
    sub_stats = lapply(subs@results, function(x) {
      stat = synGetSubmissionStatus(x$id)
      for (i in stat@annotations@stringAnnos@content) {
        if (i$key == "team") {
          team = i$value
        }
      }
      c(x$createdOn, team)
    })
    OFFSET = OFFSET + LIMIT
    challenge_stats = append(challenge_stats, sub_stats)
  }
  challenge_stats_df = data.frame(do.call(rbind, challenge_stats))
  colnames(challenge_stats_df) <- c("time","team")
  challenge_stats_df$Date = as.Date(challenge_stats_df$time)
  challenge_stats_df
}

submissionsPerWeek = function(challenge_stats_df, challengeSynId) {
  png("submissionsPerWeek.png",width = 600, height = 400)
  hist(challenge_stats_df$Date,"weeks",format="%d %b",freq = T, main="Number of Submissions Per Week", ylab="Number of Submissions",xlab="Date")
  dev.off()
  synStore(File("submissionsPerWeek.png",parentId = challengeSynId))
}

numTeamsOverTime = function(challenge_stats_df, challengeSynId) {
  weeks <- seq(min(challenge_stats_df$Date), max(challenge_stats_df$Date)+6, "weeks")
  weekSegment = sapply(challenge_stats_df$Date, function(x) {
    as.character(tail(weeks[x >= weeks],n=1))
  })
  submissions <- table(as.Date(weekSegment),challenge_stats_df$team)
  for (i in seq(2, nrow(submissions))) {
    submissions[i,] = submissions[i-1,] + submissions[i,]
  }
  numberOfTeams = rowSums(submissions > 0)
  dates = as.Date(names(numberOfTeams))
  png("totalTeamsSubmitted.png",width=600, height=400)
  plot(dates,numberOfTeams, xaxt="n",xlab = "Dates",ylab = "Number of Teams",main="Number of Teams Submitted",ylim = c(0, max(numberOfTeams)),type = "l")
  axis.Date(1, at = seq(min(dates), max(dates)+6, "weeks"))
  dev.off()
  synStore(File("totalTeamsSubmitted.png",parentId = "syn8082860"))
}

#TESLA STATS
challenge_stats_df = getSubmissionCount(8116290, "VALIDATED")
#Get submissions per week
submissionsPerWeek(challenge_stats_df, "syn8082860")
#Get cumulative teams submitted over time
numTeamsOverTime(challenge_stats_df, "syn8082860")
