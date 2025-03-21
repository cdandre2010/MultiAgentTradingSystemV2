"""
Templates for data requirements collection dialog in the ConversationalAgent.
"""

DATA_REQUIREMENTS_INITIAL_PROMPT = """
Now that we have the basic strategy components defined, let's talk about your data requirements.

Your strategy will need historical market data for backtesting and analysis. I'll help you configure the data sources and requirements.

First, let's confirm your instrument '{instrument}' and timeframe '{frequency}'. 

For backtesting, we typically need a substantial amount of historical data. How far back would you like to test your strategy? 
I recommend at least 1-2 years of data for reliable results.
"""

DATA_SOURCE_SELECTION_PROMPT = """
For the instrument {instrument} at {frequency} timeframe, we can get data from the following sources:

1. Our InfluxDB cache (fastest, if data is available)
2. Binance API (good for crypto)
3. Yahoo Finance (good for stocks)
4. Alpha Vantage (good for stocks, forex)
5. Custom data source (if you have your own data)

I'll check our InfluxDB cache first, and if the data isn't available or complete, I'll fetch it from the appropriate external source.

Do you have any preferences for external data sources? Or should I automatically select the most appropriate one?
"""

DATA_QUALITY_PROMPT = """
Let's discuss data quality requirements:

1. Should we exclude periods with volume below a certain threshold? Low volume can lead to unreliable signals.
2. How should we handle missing data? Options include: forward fill, backward fill, linear interpolation, or ignore.
3. Would you like any preprocessing applied to the data? Options include: normalization, outlier treatment, or smoothing.

These settings affect the quality of your backtest results.
"""

DATA_LOOKBACK_PERIOD_PROMPT = """
Your strategy uses {indicator_list} indicators. 

Some indicators need additional "lookback" data before your backtest start date to calculate correctly. For example, a 200-period moving average needs at least 200 bars before the start of your backtest.

Based on your indicators, I recommend a lookback period of {recommended_lookback}. 
Would you like to use this recommended lookback period or specify a different one?
"""

DATA_CONFIRMATION_PROMPT = """
Let me confirm your data configuration:

- Instrument: {instrument}
- Timeframe: {frequency}
- Date range: {start_date} to {end_date}
- Lookback period: {lookback_period}
- Primary data source: {primary_source}
- Backup sources: {backup_sources}
- Quality requirements: {quality_requirements}
- Preprocessing: {preprocessing}

Is this configuration correct? If not, what would you like to change?
"""

DATA_AVAILABILITY_REPORT = """
I've checked the data availability for your strategy:

- Instrument: {instrument}
- Timeframe: {frequency}
- Date range: {start_date} to {end_date}

Status: {status}

{details}

{recommendation}
"""

# Example availability reports
DATA_AVAILABLE_TEMPLATE = """
Good news! All the data you need is already available in our InfluxDB cache. 
We have complete data for {instrument} at {frequency} timeframe from {available_start} to {available_end}.

We can proceed with your strategy backtesting using the cached data.
"""

DATA_PARTIALLY_AVAILABLE_TEMPLATE = """
I found partial data in our InfluxDB cache:
- Available: {available_start} to {available_end}
- Missing: {missing_periods}

I'll fetch the missing data from {external_source} and cache it for future use.
This may take a moment depending on the amount of data needed.
"""

DATA_NOT_AVAILABLE_TEMPLATE = """
The data you need is not currently in our InfluxDB cache.

I'll fetch the data from {external_source} based on your requirements and cache it for future use.
This may take a moment depending on the amount of data needed.
"""