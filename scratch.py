import datetime
from collections import OrderedDict

import backtrader as bt
from intraday import StandardIntradayStrategy

class BuyTheOpenStrategy(StandardIntradayStrategy):

    def __init__(self):
        super(BuyTheOpenStrategy, self).__init__()
        self.openTimer.plotinfo.plot = True

    def handle_open(self):
        """ Called when market opens """
        self.buy()

class SMACloseSignal(bt.Indicator):
    lines = ('signal',)
    params = (('period', 30),)

    def __init__(self):
        self.lines.signal = self.data - bt.indicators.SMA(period=self.p.period)

def get_ib_store():
    store_args = dict(
        host = "127.0.0.1", # "gdc1.ibllc.com", # backup: gdc1_hb1.ibllc.com
        port = 7496,
        clientId = 721,
    )

    store = bt.stores.IBStore(**store_args)
    return store

def get_data(ibstore):
    data_args = dict(
        timeframe = bt.TimeFrame.Minutes,
        compression = 30,
        historical = True, # Set to False to do live trading
        fromdate = datetime.datetime(year=2017, month=1, day=1),
        backfill_start = True, # backfill data at the maximum possible duration at start
        backfill = True, # backfill missing data on a reconnection
    )

    contract_args = OrderedDict([
        ("symbol", "ES"),
        ("secType", "FUT"),
        ("exchange", "USD"),
        ("expiry", "201712"),
    ])
    # con = ibConnection(host='127.0.0.1', port=7496, clientId=721)
    # con.register(historical_data_handler, message.historicalData)
    # con.connect( )
    # contract = Contract(**contract_args)
    # con.reqHistoricalData(0, contract, '', '3 W', '1 hour', 'TRADES', 1, 2)

    data_args["dataname"] = "-".join(contract_args.values())
    print("dataname: {}".format(data_args["dataname"]))
    data = ibstore.getdata(**data_args)
    return data

def main():
    print("Connecting to store.")
    # Connect to Interactive Brokers
    ibstore = get_ib_store()

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set our sizer
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)
    # cerebro.addsizer(MrTimerSizer)

    # Load our data, create and add the datafeed
    print("Getting data")
    data = get_data(ibstore)
    cerebro.adddata(data)

    # Add the strategies to run
    cerebro.add_signal(bt.SIGNAL_LONGSHORT, SMACloseSignal)
    # cerebro.addstrategy(BuyTheOpenStrategy)

    # Run the backtest
    print("Running backtest")
    result = cerebro.run()

    # Plot the result
    print("Printing backtest")
    cerebro.plot()

if __name__ == "__main__":
    main()