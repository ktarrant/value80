import pytest
import logging
from unittest.mock import create_autospec, ANY

from manager import ValueAreaManager, ValueAreaOrderClient

log = logging.getLogger(__name__)

@pytest.fixture()
def vaManager(request):
    mockOrderClient = create_autospec(ValueAreaOrderClient)
    return ValueAreaManager(orderClient=mockOrderClient)

VAL = 10
VAH = 20
sample_buy_1 = ("buy", 7, 11, 21)
sample_sell_1 = ("sell", 23, 19, 9)
samples = [sample_buy_1, sample_sell_1]
sample_entries = [(bs,sP,eP) for (bs,sP,eP,_) in samples]

@pytest.mark.parametrize("buyOrSell,startPrice,entryPrice", sample_entries)
def test_valueEntryOpen(vaManager, buyOrSell, startPrice, entryPrice):
    vaManager.handleNext(VAL, VAH, startPrice, entryPrice) # stalking_below/stalking_above/idle -> value_buy

    if startPrice < VAL:
        expected_entry_price = VAL
    elif startPrice > VAH:
        expected_entry_price = VAH
    else:
        raise ValueError("invalid value area test. start price {} inside value area {}-{}".format(startPrice, VAL, VAH))

    vaManager.orderClient.update_entry_order.assert_called_with(buyOrSell, expected_entry_price)
    return vaManager

@pytest.mark.parametrize("buyOrSell,startPrice,entryPrice", sample_entries)
def test_valueAreaEntrySuccess(vaManager, buyOrSell, startPrice, entryPrice):
    vaManager = test_valueEntryOpen(vaManager, buyOrSell, startPrice, entryPrice)

    vaManager.order_filled()
    # TODO: Replace "ANY" (which suceeds for any value) with an expected stop value
    stopPrice = ANY
    log.warning("Not validating stop. Current stop: {}".format(vaManager.current_stop))
    if buyOrSell == "buy":
        targetPrice = VAH
        vaManager.orderClient.update_exit_limit.assert_called_with("sell", targetPrice)
        vaManager.orderClient.update_exit_stop.assert_called_with("sell", stopPrice)
    else:
        targetPrice = VAL
        vaManager.orderClient.update_exit_limit.assert_called_with("buy", targetPrice)
        vaManager.orderClient.update_exit_stop.assert_called_with("buy", stopPrice)
    # We're so dumb - could you tell us the stop?

    # Expect to get the candle after we get the order_filled notification
    vaManager.handleNext(VAL, VAH, entryPrice, targetPrice)

    return vaManager

@pytest.mark.parametrize("buyOrSell,startPrice,entryPrice,exitPrice", samples)
def test_valueAreaCompleteSuccess(vaManager, buyOrSell, startPrice, entryPrice, exitPrice):
    vaManager = test_valueAreaEntrySuccess(vaManager, buyOrSell, startPrice, entryPrice)
    targetPrice = VAH if buyOrSell == "buy" else VAL

    vaManager.order_filled()
    vaManager.orderClient.cancel_exit_orders.assert_called_with()

    # Expect to get the candle after we get the order_filled notification
    vaManager.handleNext(VAL, VAH, targetPrice, exitPrice)