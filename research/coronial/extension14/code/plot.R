# Standalone descriptive figures. Captions and overall titles are separate.
args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(args[1]); out <- if(length(args)>1) args[2] else file.path(root,'figures')
dir.create(out,recursive=TRUE,showWarnings=FALSE)
library(ggplot2)
read <- function(n) read.csv(file.path(root,'results',paste0(n,'.csv')),check.names=FALSE,na.strings=c('','..','na'))
theme_set(theme_bw(base_size=11,base_family="Helvetica")+theme(panel.grid.minor=element_blank(),legend.position='bottom',strip.background=element_rect(fill='grey95'),text=element_text(colour='black'),axis.text=element_text(colour='black')))
pal <- c('#0072B2','#D55E00','#009E73','#CC79A7')
export <- function(p,n,w=9,h=7) {
  # Build each plot on its own device; do not reuse device-dependent grobs.
  ggplot2::ggsave(file.path(out,paste0(n,'.png')),plot=p,width=w,height=h,
                 units='in',dpi=180,device=grDevices::png,type='cairo')
  ggplot2::ggsave(file.path(out,paste0(n,'.pdf')),plot=p,width=w,height=h,
                 units='in',device=grDevices::cairo_pdf)
}

long <- function(d,keys,groupname='Measure') {do.call(rbind,lapply(keys,function(k)data.frame(d[,setdiff(names(d),keys),drop=FALSE],Measure=k,value=d[[k]],check.names=FALSE)))}
nz <- read('nz-timeline'); nz$year <- as.numeric(substr(nz$period,1,4))+1
z <- long(nz,c('deaths_reported','jurisdiction_accepted','cases_closed','cases_on_hand_30_June','mean_days_case_closure'))
z$Panel <- ifelse(z$Measure=='mean_days_case_closure','C. Closed-case mean (days)',ifelse(z$Measure=='cases_on_hand_30_June','B. Pending at 30 June (cases)','A. Annual activity (cases)'))
z$Measure <- factor(z$Measure,levels=c('deaths_reported','jurisdiction_accepted','cases_closed','cases_on_hand_30_June','mean_days_case_closure'),labels=c('Deaths reported','Jurisdiction accepted','Cases closed','Pending','Mean duration'))
# Older duration definitions are isolated points; only recent means are connected.
connect <- z[z$Panel!='C. Closed-case mean (days)' | z$year>=2021,]
export(ggplot(z,aes(year,value,colour=Measure))+geom_line(data=connect)+geom_point(size=1.5)+facet_wrap(~Panel,ncol=1,scales='free_y')+scale_colour_manual(values=c(pal,'#000000'))+scale_x_continuous(breaks=c(2015,2017,2019,2021,2023,2025))+labs(x='Financial year ending June',y=NULL),'01-nz-timeline',9,8)
a <- read('australia-longitudinal'); a$year <- as.numeric(substr(a$period,1,4))+1
plotau <- function(d,y) ggplot(d,aes(year,value,colour=metric,group=interaction(metric,segment)))+geom_line(na.rm=TRUE)+geom_point(size=1,na.rm=TRUE)+facet_wrap(~jurisdiction,ncol=4,scales='free_y')+scale_colour_manual(values=pal)+scale_x_continuous(breaks=c(2016,2019,2022,2025))+labs(x='Financial year ending June',y=y,colour=NULL)
export(plotau(subset(a,measure=='Backlog' & unit=='%' & metric %in% c('Cases >12 months','Cases >24 months')),'Share of pending cases (%)'),'02-australia-backlog-age',11,7)
export(plotau(subset(a,metric=='Clearance indicator' & unit=='%'),'Published clearance indicator (%)'),'03-australia-clearance',11,7)
f <- subset(a,measure %in% c('Lodgments','Finalisations') & stratum=="Total coroners' courts (incl. deaths and fires reported)" & unit=='no.')
f$metric <- f$measure
export(plotau(f,'Death and fire cases (count)'),'04-australia-activity',11,7)
n <- read('niio-monthly'); n$date <- as.Date(paste(n$year,match(n$month,month.name),'01',sep='-'))
n$advice_share_percent <- 100*n$advice_cases/n$total_cases
nn <- long(n,c('advice_cases','coronial_cases','advice_share_percent')); nn$Panel <- ifelse(nn$Measure=='advice_share_percent','B. Advice share of filings (%)','A. Filing cohorts (cases)')
nn$Measure <- factor(nn$Measure,levels=c('advice_cases','coronial_cases','advice_share_percent'),labels=c('Advice','Coronial','Advice share'))
export(ggplot(nn,aes(date,value,colour=Measure))+geom_line()+facet_wrap(~Panel,ncol=1,scales='free_y')+scale_colour_manual(values=pal)+labs(x='First application filing month',y=NULL),'05-niio-monthly',9,7)
ag <- read('niio-age-annual'); ag$year <- ifelse(ag$year==2021,'2021 Jan-Jun',as.character(ag$year)); ag$age_group <- factor(ag$age_group,levels=rev(unique(ag$age_group)))
export(ggplot(ag,aes(year,age_group,fill=share_percent))+geom_tile(colour='white')+scale_fill_gradient(low='white',high='#0072B2',name='Share (%)')+labs(x='Filing cohort; classified at 19 July 2021',y='Age group (years)'),'06-niio-age',8,7)
b <- read('funding-components'); b$year <- as.numeric(substr(b$fiscal_year,1,4))+1
b$measure <- factor(b$measure,levels=c('coroner_salary_allowances','coroner_directed_postmortems'),labels=c('Coroner salary and allowances component','Coroner-directed postmortems component'))
# Use original category names in captions, not an inferred service-wide budget.
export(ggplot(subset(b,basis!='estimated_actual'),aes(year,value_NZD_thousands/1000,colour=basis,group=basis))+geom_line()+geom_point()+facet_wrap(~measure,ncol=1,scales='free_y')+scale_colour_manual(values=pal,labels=c('Final budget in following edition','Original budget'))+labs(x='Financial year ending June',y='Nominal NZ$ million',colour='Budget basis'),'07-funding-components',9,7)
e <- subset(read('england-wales-national'),year>=1995)
el <- long(e,c('registered_deaths','reported_deaths','inquests_opened','postmortems'))
el$Measure <- factor(el$Measure,levels=c('registered_deaths','reported_deaths','inquests_opened','postmortems'),labels=c('Deaths registered','Deaths reported','Inquests opened','Postmortems'))
export(ggplot(el,aes(year,value,colour=Measure))+geom_line()+scale_colour_manual(values=pal)+scale_y_continuous(labels=function(x)format(x,big.mark=',',scientific=FALSE,trim=TRUE))+labs(x='Calendar year; 2024 revised, 2025 provisional',y='Count',colour=NULL),'08-england-wales-activity',9,6)
v <- subset(read('international-context'),jurisdiction=='Victoria' & metric=='mean_closed_investigation_duration')
v$year <- as.numeric(substr(v$period,1,4))+1
ed <- read('england-wales-inquest-time')
d <- rbind(data.frame(year=nz$year[nz$year>=2021],value=nz$mean_days_case_closure[nz$year>=2021],Panel='NZ: mean closed-case duration (days)'),data.frame(year=v$year,value=v$value,Panel='Victoria: closed investigations (days)'),data.frame(year=ed$year,value=as.numeric(ed$displayed_weeks),Panel='England and Wales: estimated inquest time (weeks)'))
limits <- data.frame(year=c(2021,2025,2021,2025,2023,2025),value=c(0,700,0,400,0,40),Panel=rep(c('NZ: mean closed-case duration (days)','Victoria: closed investigations (days)','England and Wales: estimated inquest time (weeks)'),each=2))
export(ggplot(d,aes(year,value))+geom_blank(data=limits)+geom_line(colour=pal[1])+geom_point(colour=pal[1])+facet_wrap(~Panel,ncol=1,scales='free')+scale_x_continuous(breaks=2021:2025)+labs(x='Year ending June for NZ/Victoria; calendar year for England/Wales',y=NULL),'09-duration-contexts',9,8)
writeLines(c(R.version.string,paste('ggplot2',as.character(packageVersion('ggplot2'))),capture.output(sessionInfo())),file.path(out,'runtime.txt'))

h <- read('historical-ris'); h$year <- as.numeric(substr(h$period,1,4))+1
h$Panel <- ifelse(grepl('^mean_days',h$metric),'B. Mean days by closure route','A. Counts by reported route')
h$metric <- gsub('_',' ',h$metric)
export(ggplot(h,aes(year,value,colour=metric,group=metric))+geom_line()+geom_point()+facet_wrap(~Panel,ncol=1,scales='free_y')+scale_x_continuous(breaks=2008:2012)+guides(colour=guide_legend(ncol=2))+labs(x='Financial year ending June',y=NULL,colour=NULL),'10-historical-nz-routes',10,8)
