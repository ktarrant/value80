import backtrader as bt
import pandas as pd
import datetime as dt

from intraday import StandardIntradayStrategy

class BuyTheOpenStrategy(StandardIntradayStrategy):

    def __init__(self):
        super(BuyTheOpenStrategy, self).__init__()
        self.openTimer.plotinfo.plot = True

    def handle_open(self):
        """ Called when market opens """
        self.buy()

def get_csv_data():
    df = pd.read_csv("ES.csv")
    df["datetime"] = df["datetime"].apply(lambda ts: dt.datetime.strptime(ts, "%Y%m%d %H:%M:%S"))
    df = df.set_index("datetime")
    return bt.feeds.PandasData(dataname=df)

def main():
    # Create a cerebro entity
    cerebro = bt.Cerebro( )

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set our sizer
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)
    # cerebro.addsizer(MrTimerSizer)

    # Load our data, create and add the datafeed
    data = get_csv_data()
    cerebro.adddata(data)

    # Add the strategies to run
    cerebro.addstrategy(BuyTheOpenStrategy)

    # Run the backtest
    result = cerebro.run()

    # Plot the result
    cerebro.plot()

if __name__ == "__main__":
    main()