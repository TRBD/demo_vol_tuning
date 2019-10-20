library(rugarch)
library(xts)


rGARCH <- function(data, dt.test.start, dt.test.end, vModel, nForecastDays=21, nSimulations=5000, dist="norm")
{
	result.list = list()
    if (is.data.frame(data))
	{
		dt.test.start <- as.Date(dt.test.start)
        dt.test.end <- as.Date(dt.test.end)
		dates   <- as.Date(data$Date, "%m/%d/%Y")
		prices.xts <- as.xts(data$Close, order.by=dates)
		
		# filter price dates past test date
        prices.xts.past = prices.xts[paste(as.character(dt.test.start), "/", as.character(dt.test.end),sep="")]
        
		# filter price dates prior test date
        prices.xts.fut = prices.xts[paste(as.character(dt.test.end), "/",sep="")]
	    
		# test date truncated return set
      	returns.xts.past = na.omit(diff(log(prices.xts.past),1))

        # test date truncated return set
      	returns.xts.fut = na.omit(diff(log(prices.xts.fut),1))
        
		# Define the GARCH model
		uspec <- ugarchspec(variance.model = list(model=vModel, garchOrder=c( 1,1 ), submodel=NULL),
				mean.model=list(armaOrder=c( 0,0 ),
						include.mean=TRUE),distribution.model=dist)
        
		# fit the GARCH model
		fit.garch = ugarchfit(spec = uspec, data = returns.xts.past, solver="hybrid")
		result.list = list()

        # simulate the model forward
        sim  = ugarchsim(fit.garch, n.sim=nForecastDays, n.start=0, m.sim=nSimulations, startMethod="sample")

        # calculate the RMS of the simulated returns
        sims =  sqrt((colSums(fitted(sim)^2, na.rm=T)))
        sims.sorted = sort(sims)
        # filter out the most extreme 5% of values
        cut.lo = as.integer(nSimulations * .025)
        cut.hi = as.integer(nSimulations * .975)
        sims.cut = sims.sorted[cut.lo:cut.hi]
        # annualize
        sim.ann      = sqrt(252 / (nForecastDays-1)) * sims.cut
        mean.sim.ann = mean(sim.ann)

        qnt = quantile(sim.ann)

        ret.future = head(returns.xts.fut, nForecastDays)
        vol.realized = sqrt(sum(ret.future^2) / (nForecastDays-1))
        vol.realized.ann = sqrt(252) * vol.realized

        forecast.error = vol.realized.ann - mean.sim.ann

        prefix = paste(vModel, dist, as.character(nSimulations),
            as.character(nForecastDays), strftime(dt.test.start,'%Y%m%d'), strftime(dt.test.end,'%Y%m%d'), sep='_')
        result.list[[paste(prefix, 'quantile0', sep='_')]] = qnt[[1]]
        result.list[[paste(prefix, 'quantile25', sep='_')]] = qnt[[2]]
        result.list[[paste(prefix, 'quantile50', sep='_')]] = qnt[[3]]
        result.list[[paste(prefix, 'quantile75', sep='_')]] = qnt[[4]]
        result.list[[paste(prefix, 'quantile100', sep='_')]] = qnt[[5]]
        result.list[[paste(prefix, 'mean.sim.ann', sep='_')]] = mean.sim.ann
        result.list[[paste(prefix, 'vol.realized.ann', sep='_')]] = vol.realized.ann
        result.list[[paste(prefix, 'forecast.error', sep='_')]] = forecast.error
    }
	return(result.list)
}