library(data.table)
library(ggplot2)
participants = read.csv("~/sage_projects/DREAM/statistics/participation.csv")
participants$Year = as.character(participants$Year)
participants$Year=factor(participants$Year,levels=c('2016','2015',"2014","2013"))
participants$indexing = c(1:17)
seq_along(participants)
ggplot(participants, aes(x=reorder(Name,-indexing),y=Number,fill=Year))+ geom_bar(stat="identity") + coord_flip() +
  ylab("Number of Participants") +
  theme(axis.text.y = element_text(size=16),
        axis.title.y=element_blank(),
        axis.text.x  = element_text(size=16),
        title = element_text(size=16),
        legend.text=element_text(size=12),legend.justification=c(1,0), 
        legend.position=c(1,0))

ggsave("~/sage_projects/DREAM/statistics/challenge_participation_2013-2016.pdf",width=15,height=8)
