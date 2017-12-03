import logging
import numpy as np
import backtrader as bt
from transitions import Machine

from levels import VALUE_AREAS

log = logging.getLogger(__name__)

class ValueAreaOrderClient(object):

    def update_entry_order(self, buyOrSell, price):
        raise NotImplementedError("update_entry_order not implemented")

    def cancel_entry_order(self):
        raise NotImplementedError("cancel_entry_order not implemented")

    def update_exit_limit(self, buyOrSell, price):
        raise NotImplementedError("update_exit_limit not implemented")

    def update_exit_stop(self, buyOrSell, price):
        raise NotImplementedError("update_exit_stop not implemented")

    def cancel_exit_orders(self):
        raise NotImplementedError("cancel_exit_orders not implemented")

    def close_all_positions(self):
        raise NotImplementedError("cancel_exit_orders not implemented")



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

    def close_all_positions_and_orders(self):
        if self.orderClient:
            self.orderClient.cancel_entry_order()
            self.orderClient.cancel_exit_orders()
            self.orderClient.close_all_positions()
        else:
            log.error("close_all_positions_and_orders called without orderClient")

    def update_entry_order(self):
        if self.orderClient:
            if self.state == "value_buy":
                target = self.VAL
                if np.isnan(target):
                    log.error("Buy entry order requested with NaN VAL")
                else:
                    self.orderClient.update_entry_order("buy", target)
            elif self.state == "value_sell":
                target = self.VAH
                if np.isnan(target):
                    log.error("Sell entry order requested with NaN VAH")
                else:
                    self.orderClient.update_entry_order("sell", target)
            else:
                log.error("Entry requested during invalid state: {}".format(self.state))
        else:
            log.error("update_entry_order called without orderClient")

    def cancel_entry_order(self):
        if self.orderClient:
            self.orderClient.cancel_entry_order()
        else:
            log.error("cancel_entry_order called without orderClient")

    def update_closing_orders(self):
        if self.orderClient:
            if self.state == "value_buy_hold":
                target = self.VAH
                stop = self.VAL * 0.99 # TODO: MAKE THE STOP CONFIGURABLE SOMEHOW

                if np.isnan(target) or np.isnan(stop):
                    raise ValueError("Buy closing order requested with NaN VAL or VAH")

                self.orderClient.update_exit_limit("sell", target)
                self.orderClient.update_exit_stop("sell", stop)

            elif self.state == "value_sell_hold":
                target = self.VAL
                stop = self.VAH * 1.01 # TODO: MAKE THE STOP CONFIGURABLE SOMEHOW

                if np.isnan(target) or np.isnan(stop):
                    raise ValueError("Sell closing order requested with NaN VAL or VAH")

                self.orderClient.update_exit_limit("buy", target)
                self.orderClient.update_exit_stop("buy", stop)

            else:
                log.error("Exit requested during invalid state: {}".format(self.state))

        else:
            log.error("update_closing_orders called without orderClient")

    def cancel_closing_orders(self):
        if self.orderClient:
            self.orderClient.cancel_closing_orders()
        else:
            log.error("cancel_closing_orders called without orderClient")

    def __init__(self, orderClient=None):
        self.orderClient = orderClient

        # Build the state machine
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

        # Position management
        self.machine.add_transition(source="value_buy_hold", trigger="order_filled", dest="stalking_above",
                                    conditions=["is_candle_close_above_VAH"],
                                    before="cancel_closing_orders")
        self.machine.add_transition(source="value_buy_hold", trigger="order_filled", dest="stalking_inside",
                                    conditions=["is_candle_close_below_VAH", "is_candle_close_above_VAL"],
                                    before="cancel_closing_orders")
        self.machine.add_transition(source="value_buy_hold", trigger="order_filled", dest="stalking_below",
                                    conditions=["is_candle_close_above_VAL"],
                                    before="cancel_closing_orders")
        self.machine.add_transition(source="value_buy_hold", trigger="order_cancelled", dest="value_buy_hold")

        self.machine.add_transition(source="value_sell_hold", trigger="order_filled", dest="stalking_above",
                                    conditions=["is_candle_close_above_VAH"],
                                    before="cancel_closing_orders")
        self.machine.add_transition(source="value_sell_hold", trigger="order_filled", dest="stalking_inside",
                                    conditions=["is_candle_close_below_VAH", "is_candle_close_above_VAL"],
                                    before="cancel_closing_orders")
        self.machine.add_transition(source="value_sell_hold", trigger="order_filled", dest="stalking_below",
                                    conditions=["is_candle_close_above_VAL"],
                                    before="cancel_closing_orders")

        # Initialize state variables
        self.reset()

    def reset(self):
        self.state = "idle"
        self.VAH = np.NaN
        self.VAL = np.NaN
        self.candle_open = np.NaN
        self.candle_close = np.NaN

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
