import backtrader as bt
import pandas as pd
import numpy as np
import datetime
import logging

from intraday import OutputEventTimer
from levels import VALUE_AREAS

log = logging.getLogger(__name__)

class ValueAreaIndicator(bt.Indicator):
    lines = ("high", "low")
    params = (
        ("symbol", ""),
    )

    def next(self):
        try:
            levelHistory = VALUE_AREAS[self.p.symbol]
        except KeyError:
            self.lines.high[0] = np.NaN
            self.lines.low[0] = np.NaN
            return

        curdate = self.data.datetime.date()
        try:
            levels = levelHistory[curdate]
        except KeyError:
            self.lines.high[0] = np.NaN
            self.lines.low[0] = np.NaN
            return

        self.lines.high[0] = levels["VAH"]
        self.lines.low[0] = levels["VAL"]

class ValueAreaStrategy(bt.Strategy):
    params = (
        ('close_offset', 30),
        ("symbol", ""),
    )

    valid_states = ["none", "inside", "below", "above"]

    # TODO: Add price to alert
    _CANDLE_ALERT_MSG = "{symbol} trade opportunity @ {date} {time}: {open_state} -> {close_state}"

    def __init__(self):
        super(ValueAreaStrategy, self).__init__()
        self.openTimer = OutputEventTimer(offset=0)
        self.closeTimer = OutputEventTimer(base="close", offset=-self.p.close_offset)
        self.valueArea = ValueAreaIndicator(symbol=self.p.symbol, subplot=False)
        self._last_state = "none"

    def base(self, state):
        return state.split( )[0]

    @property
    def last_state(self):
        return self._last_state

    @last_state.setter
    def last_state(self, value):
        state = self.base(value)
        if not state in self.valid_states:
            raise ValueError("invalid state '{}'.".format(value))
        self._last_state = value

    def nextstart(self):
        self.order = None
        self.next()

    def _get_state(self, source="close"):
        if pd.isnull(self.valueArea.lines.high[0]) or pd.isnull(self.valueArea.lines.low[0]):
            return "none"
        else:
            hi = self.valueArea.lines.high[0]
            lo = self.valueArea.lines.low[0]
            cur = getattr(self.data, source)[0]
            if cur > hi:
                rv = "above VAH ({})".format(hi)
            elif cur < lo:
                rv = "below VAL ({})".format(lo)
            else:
                rv = "inside VA ({}-{})".format(lo, hi)
            return rv

    def manage_current_trade(self):
        pass

    def next(self):
        if self.openTimer.lines.event[0] == True:
            # It's a new day! Reset the "last" status
            self.last_state = "none"

        state = self._get_state()
        open_state = self._get_state(source="open")
        if self.base(state) == self.base(open_state):
            self.manage_current_trade()
        else:
            msg = self._CANDLE_ALERT_MSG.format(
                symbol=self.p.symbol, open_state=open_state, close_state=state,
                date=self.data.datetime.date(), time=self.data.datetime.time(),
            )
            log.warning(msg)

        self.last_state = state

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
    cerebro.addstrategy(ValueAreaStrategy, symbol="ESZ7")
    # Run the backtest
    result = cerebro.run()

    # Plot the result
    # cerebro.plot()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()