import numpy as np
import backtrader as bt
from transitions import Machine

from levels import VALUE_AREAS

class ValueAreaManager(object):

    states = [
        "idle", # no orders open, no open position, no awareness of current market conditions or VA levels invalid
        "stalking_above", # no orders open, no open position, price above VAH
        "stalking_below", # no orders open, no open position, price below VAL
        "stalking_inside", # no orders open, no open position, price inside VA
        "value_buy", # price is near VAL, no open position, attempting to open a long position
        "value_buy_hold", # managing a long position inside the value area
        "value_sell", # price is near VAH, no open position, attempting to open a short position
        "value_sell_hold", # manage a short position inside the value area
    ]

    def __init__(self):
        self.VAH = np.NaN
        self.VAL = np.NaN
        self.candle_open = np.NaN
        self.candle_close = np.NaN

        self.machine = Machine(model=self, states=ValueAreaManager.states, initial="idle")

        # From any state, if we don't have Value Area data then close out everything and go all cash
        self.machine.add_transition(source="*", trigger="next", dest="idle",
                                    conditions=["is_VA_null"],
                                    before="close_all_positions_and_orders",
                                    )

        # Transitions from idle
        self.machine.add_transition(source="idle", trigger="next", dest="stalking_below",
                                    conditions=["is_candle_close_below_VAL"])
        self.machine.add_transition(source="idle", trigger="next", dest="stalking_above",
                                    conditions=["is_candle_close_above_VAH"])
        self.machine.add_transition(source="idle", trigger="next", dest="stalking_inside",
                                    conditions=[
                                        "is_candle_close_below_VAH", "is_candle_open_below_VAH",
                                        "is_candle_close_above_VAL", "is_candle_open_above_VAL",
                                    ])
        self.machine.add_transition(source="idle", trigger="next", dest="value_buy",
                                    conditions=["is_candle_close_above_VAL", "is_candle_open_below_VAL"],
                                    after="update_entry_order")
        self.machine.add_transition(source="idle", trigger="next", dest="value_sell",
                                    conditions=["is_candle_close_below_VAH", "is_candle_open_above_VAH"],
                                    after="update_entry_order")

        # Transitions from stalking
        self.machine.add_transition(source="stalking_below", trigger="next", dest="value_buy",
                                    conditions=["is_candle_close_above_VAL", "is_candle_close_below_VAH"],
                                    after="update_entry_order")
        self.machine.add_transition(source="stalking_below", trigger="next", dest="stalking_above",
                                    conditions=["is_candle_close_above_VAH"])
        self.machine.add_transition(source="stalking_above", trigger="next", dest="value_sell",
                                    conditions=["is_candle_close_below_VAH", "is_candle_close_above_VAL"],
                                    after="update_entry_order")
        self.machine.add_transition(source="stalking_above", trigger="next", dest="stalking_below",
                                    conditions=["is_candle_close_below_VAL"])

        # Value area entry management
        self.machine.add_transition(source="value_buy", trigger="order_filled", dest="value_buy_hold",
                                    after="update_closing_orders")
        self.machine.add_transition(source="value_buy", trigger="order_cancelled", dest="stalking_below",
                                    conditions=["is_candle_close_below_VAL"])
        self.machine.add_transition(source="value_buy", trigger="order_cancelled", dest="value_buy",
                                    conditions=["is_candle_close_above_VAL", "is_candle_close_below_VAH"],
                                    after="update_entry_order")
        self.machine.add_transition(source="value_buy", trigger="next", dest="stalking_above",
                                    conditions=["is_candle_close_above_VAH"],
                                    before="cancel_entry_order")

        self.machine.add_transition(source="value_sell", trigger="order_filled", dest="value_sell_hold",
                                    after="update_closing_orders")
        self.machine.add_transition(source="value_sell", trigger="order_cancelled", dest="stalking_above",
                                    conditions=["is_candle_close_above_VAH"])
        self.machine.add_transition(source="value_sell", trigger="order_cancelled", dest="value_sell",
                                    conditions=["is_candle_close_above_VAL", "is_candle_close_below_VAH"],
                                    after="update_entry_order")
        self.machine.add_transition(source="value_sell", trigger="next", dest="stalking_below",
                                    conditions=["is_candle_close_below_VAL"],
                                    before="cancel_entry_order")


    def is_VA_null(self):
        return np.isnan(self.VAH) or np.isnan(self.VAL)

    def is_candle_close_below_VAL(self):
        return self.candle_close < self.VAL

    def is_candle_close_above_VAL(self):
        return self.candle_close > self.VAL

    def is_candle_close_below_VAH(self):
        return self.candle_close < self.VAH

    def is_candle_close_above_VAH(self):
        return self.candle_close > self.VAH

    def is_candle_open_below_VAL(self):
        return self.candle_open < self.VAL

    def is_candle_open_above_VAL(self):
        return self.candle_open > self.VAL

    def is_candle_open_below_VAH(self):
        return self.candle_open < self.VAH

    def is_candle_open_above_VAH(self):
        return self.candle_open > self.VAH
