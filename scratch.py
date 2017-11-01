from backtrader import Cerebro
from backtrader.sizers import PercentSizer

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
    cerebro = Cerebro( )

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set our sizer
    cerebro.addsizer(PercentSizer, percents=90)
    # cerebro.addsizer(MrTimerSizer)

    # Load our data, create and add the datafeed
    # TODO: Load IB intraday data


    # Add the strategies to run
    cerebro.addstrategy(BuyTheOpenStrategy)
    # Run the backtest
    result = cerebro.run()

    # Plot the result
    cerebro.plot()

if __name__ == "__main__":
    pass