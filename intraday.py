import datetime
import pandas as pd
from backtrader.indicator import Indicator
from backtrader import Strategy

from pandas_market_calendars import get_calendar

class StandardIntradayStrategy(Strategy):
    """ automatically closes all positions at end of day """
    params = (
        ('open_offset', 30),
        ('close_offset', 30),
    )

    def __init__(self):
        self.openTimer = OutputEventTimer(offset=self.p.open_offset)
        self.openTimer.plotinfo.plot = False
        self.closeTimer = OutputEventTimer(base='close', offset=-self.p.close_offset)
        self.closeTimer.plotinfo.plot = False

    def tobps(self, value):
        return value / self.data0.close * 10000

    def nextstart(self):
        self.order = None
        self.next()

    def next(self):
        if self.order:
            # Already have pending order
            return

        self.compute_factors()

        if self.openTimer.lines.event[0]:
            self.handle_open()

        if not self.position:

            if self.openTimer.lines.phase[0] and not self.closeTimer.lines.phase[0]:

                if self.check_for_entry():
                    self.order = self.buy()
        else:

            if self.closeTimer.lines.event[0]:
                self.order = self.close()

            elif self.check_for_stop():
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # The order was either completed or failed in some way
        self.order = None

    def handle_open(self):
        """ Called when the market is open """
        pass

    def compute_factors(self):
        """ Method for calculating intermediate factors """
        pass

    def check_for_entry(self):
        """ True if entry signal is triggered, else False """
        return False

    def check_for_stop(self):
        """ True if exit signal is triggered, else False """
        return False

class MarketOpenTimer(Indicator):
    lines = ('open', 'close')
    params = (
        ('exchange', 'NYSE'),
    )

    def __init__(self):
        self.calendar = get_calendar(self.p.exchange)
        self.lastdate = datetime.date.min  # use this as a cache

    def convert_naive_ts(self, ts):
        try:
            return pd.Timestamp.tz_convert(pd.Timestamp.tz_localize(ts, 'utc'), self.calendar.tz)
        except TypeError:
            return pd.Timestamp.tz_convert(ts, self.calendar.tz)


    def next(self):
        curdate = self.data.datetime.date()
        if curdate > self.lastdate:
            self.lastdate = curdate
            curdt = curdate.isoformat()
            schedule = self.calendar.schedule(start_date=curdt, end_date=curdt)
            self.open_dt = self.convert_naive_ts(schedule.iloc[0, 0])
            self.close_dt = self.convert_naive_ts(schedule.iloc[0, 1])

        self.lines.open[0] = self.data.date2num(self.open_dt)
        self.lines.close[0] = self.data.date2num(self.close_dt)


class EventTimer(Indicator):
    params = (
        ('exchange', 'NYSE'),
        ('base', 'open'),
        ('offset', 0), # in minutes
    )

    def __init__(self):
        self.marketTimer = MarketOpenTimer(self.data, exchange=self.p.exchange)

    def get_offset_delta(self):
        return datetime.timedelta(minutes=self.p.offset)

    def next(self):
        base_value = getattr(self.marketTimer.lines, self.p.base)[0]
        base_dt = self.marketTimer.convert_naive_ts(pd.Timestamp(self.data.num2date(base_value)))
        trigger_dt = base_dt + self.get_offset_delta()
        curdatetime = pd.Timestamp(self.data.datetime.datetime()).tz_localize(
            self.marketTimer.calendar.tz)
        if curdatetime == trigger_dt:
            self.trigger_start()

        elif curdatetime > trigger_dt:
            self.trigger()

        else:
            self.off()

    def trigger_start(self):
        self.trigger()

    def trigger(self):
        pass

    def off(self):
        pass

class OutputEventTimer(EventTimer):
    lines = ('event', 'phase')
    params = (
        ('trigger', True),
        ('off', False),
    )

    def trigger_start(self):
        self.lines.event[0] = self.p.trigger
        self.lines.phase[0] = self.p.trigger

    def trigger(self):
        self.lines.event[0] = self.p.off
        self.lines.phase[0] = self.p.trigger

    def off(self):
        self.lines.event[0] = self.p.off
        self.lines.phase[0] = self.p.off

class RangeEventTimer(EventTimer):
    lines = ('high', 'low')
    params = (
        ('period', 1),
    )
    plotinfo = dict(subplot=False)

    def __init__(self):
        super(RangeEventTimer, self).__init__()
        self.addminperiod(self.p.period)

    def get_offset_delta(self):
        return datetime.timedelta(minutes=self.p.offset + self.p.period - 1)

    def trigger_start(self):
        self.high = max(self.data.high.get(size=self.p.period))
        self.low = min(self.data.low.get(size=self.p.period))
        self.trigger()

    def trigger(self):
        self.lines.high[0] = self.high
        self.lines.low[0] = self.low
