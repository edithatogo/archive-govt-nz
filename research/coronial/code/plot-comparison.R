args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else '.'
p <- file.path(root,'results')
d <- read.csv(file.path(root,'data','australian-coronial-observations.csv'),stringsAsFactors=FALSE,check.names=FALSE)
years <- paste0(2020:2024,'-',21:25)
regions <- c('NSW','Vic','Qld','WA','SA','Tas','ACT','NT')
make <- function(metric,table) {
 m <- matrix(NA_real_,nrow=8,ncol=5,dimnames=list(regions,years))
 for(i in seq_along(regions))for(j in seq_along(years)) {
  # Explicit column lookup avoids R NSE name collisions below.
  a<-d[d$jurisdiction==regions[i]&d$period==years[j]&d$metric==metric&d$table==table&d$unit=='%',]
  stopifnot(nrow(a)==1);m[i,j]<-a$value
 }
 m
}
a<-make('Cases >24 months','7A.21');b<-make('Clearance indicator','7A.26')
stopifnot(!anyNA(a),!anyNA(b));write.csv(data.frame(jurisdiction=rep(regions,each=5),period=rep(years,8),active_over24_pct=as.vector(t(a)),clearance_pct=as.vector(t(b))),file.path(p,'figure2-data.csv'),row.names=FALSE)
blue<-colorRampPalette(c('#F1F5F9','#BED7E4','#B0CEDD','#92B8CC'))(101)
div<-colorRampPalette(c('#BC6C4B','#F8F5EF','#3E8091'))(101)
panel<-function(m,title,sub,colours,limits) {
 par(mar=c(3.7,3.0,3.8,0.4),xaxs='i',yaxs='i')
 plot(NA,xlim=c(.5,5.5),ylim=c(.5,8.5),axes=FALSE,xlab='',ylab='',bty='n')
 for(i in 1:8)for(j in 1:5){
  v<-m[i,j];k<-max(1,min(101,round(1+100*(v-limits[1])/diff(limits))))
  rect(j-.485,8.5-i,j+.485,9.5-i,col=colours[k],border='white',lwd=1)
  rgb<-col2rgb(colours[k])/255;lum<-sum(rgb*c(.2126,.7152,.0722))
  text(j,9-i,sprintf('%.1f',v),cex=.89,col='black')
 }
 axis(1,at=1:5,labels=years,tick=FALSE,cex.axis=.70,line=-.1,gap.axis=-1)
 axis(2,at=8:1,labels=regions,tick=FALSE,las=1,cex.axis=.85,line=-.4)
 title(main=title,adj=0,cex.main=.91,line=2.1,col.main='black')
 mtext(sub,side=3,adj=0,line=.55,cex=.7,col='black')
}
render<-function(){
 par(family='Times New Roman',oma=c(3.1,.1,1.0,.1),mfrow=c(1,2),bg='white')
 panel(a,'A  Older cases still open','% of active cases older than 24 months',blue,c(0,35))
 panel(b,'B  Annual clearance','Finalisations / lodgements x 100 (%)',div,c(65,135))
 mtext('Australian coroners courts: published workload indicators',outer=TRUE,side=3,line=-.1,adj=0,cex=.95,font=2,col='black')
 mtext('Published court totals include fire matters; backlog is not death-stratified. No country ranking.',outer=TRUE,side=1,line=1.0,adj=0,cex=.69,col='black')
 mtext('A: caseload at 30 June. B: financial-year throughput; 100 means finalisations matched new lodgements.',outer=TRUE,side=1,line=2.0,adj=0,cex=.69,col='black')
}
png(file.path(p,'figure2.png'),width=2100,height=1335,res=300,type='cairo');render();dev.off()
cairo_pdf(file.path(p,'figure2.pdf'),width=7,height=4.45,family='Times New Roman');render();dev.off()
svg(file.path(p,'figure2.svg'),width=7,height=4.45);render();dev.off()
