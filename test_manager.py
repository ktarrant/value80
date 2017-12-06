import pytest
from unittest.mock import create_autospec, ANY

from manager import ValueAreaManager, ValueAreaOrderClient

@pytest.fixture()
def vaManager(request):
    mockOrderClient = create_autospec(ValueAreaOrderClient)
    return ValueAreaManager(orderClient=mockOrderClient)


def test_easyLong(vaManager):
    VAL = 10
    VAH = 20

    vaManager.handleNext(VAL, VAH, 5, 7) # idle -> stalking_below
    vaManager.handleNext(VAL, VAH, 7, 11) # stalking_below -> value_buy
    vaManager.orderClient.update_entry_order.assert_called_with("buy", VAL)

    vaManager.handleNext(VAL, VAH, 11, 10) # this does not trigger new state! only order_filled does that
    vaManager.orderClient.update_exit_limit.assert_not_called()
    vaManager.orderClient.update_exit_stop.assert_not_called()

    vaManager.order_filled()
    vaManager.orderClient.update_exit_limit.assert_called_with("sell", VAH)
    # TODO: Replace "ANY" (which suceeds for any value) with an expected stop value
    vaManager.orderClient.update_exit_stop.assert_called_with("sell", ANY)
    # We're so dumb - could you tell us the stop?
    print(vaManager.current_stop)

    vaManager.handleNext(VAL, VAH, 10, 17)

    vaManager.order_filled()
    vaManager.orderClient.cancel_exit_orders.assert_called_with()

    vaManager.handleNext(VAL, VAH, 17, 21)


