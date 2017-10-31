import datetime
import pandas as pd
from collections import OrderedDict

from backtrader import Strategy
from backtrader.indicator import Indicator
from backtrader.sizer import Sizer

from pandas_market_calendars import get_calendar

class IntradayTimerStrategy(Strategy):
    params = (
        ('open_wait_mins', 50),  # anticipate 10:30 boys
        ('close_early_mins', 30),  # get out before 3:45 to 4:00 madness starts
    )

    def __init__(self):
        self.open_timer = self.add_timer(when=datetime.time(9,30),
                       offset=datetime.timedelta(minutes=self.params.open_wait_mins))
        self.close_timer = self.add_timer(when=datetime.time(16,00),
                       offset=datetime.timedelta(minutes=-self.params.close_early_mins))
        self.market_open = False

    def notify_timer(self, timer, when, *args, **kwargs):
        if timer == self.open_timer:
            print("handle open: {}".format(when))
            self.market_open = True

        elif timer == self.close_timer:
            print("handle close: {}".format(when))
            self.market_open = False

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
