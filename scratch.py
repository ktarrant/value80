import backtrader as bt
import pandas as pd
import datetime

from intraday import StandardIntradayStrategy


class BuyTheOpenStrategy(StandardIntradayStrategy):

    def __init__(self):
        super(BuyTheOpenStrategy, self).__init__()
        self.openTimer.plotinfo.plot = True

    def handle_open(self):
        """ Called when market opens """
        self.buy()



def main():
    # Create a cerebro entity
    cerebro = bt.Cerebro( )

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set our sizer
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)
    # cerebro.addsizer(MrTimerSizer)

    # Load our data, create and add the datafeed
    data = pd.read_csv("ES.csv")
    data["datetime"] = pd.to_datetime(data["datetime"])
    data = data.set_index("datetime")
    feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(feed)

    # Add the strategies to run
    cerebro.addstrategy(BuyTheOpenStrategy)
    # Run the backtest
    result = cerebro.run()

    # Plot the result
    cerebro.plot()

if __name__ == "__main__":
    main()