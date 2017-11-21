import logging

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

log = logging.getLogger(__name__)

class HistoryWrapper(EWrapper):
    """ The IBApi.EWrapper interface is the mechanism through which the TWS delivers information to
    the API client application. """

    def __init__(self):
        pass

class HistoryClient(EClient):

    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

class HistoryApp(HistoryWrapper, HistoryClient):

    def __init__(self):
        HistoryWrapper.__init__(self)
        HistoryClient.__init__(self, wrapper=self)

        self._is_connected = False

    def nextValidId(self, orderId):
        if not self._is_connected:
            # IBApi.EWrapper.nextValidID callback is commonly used to indicate that the connection
            # is completed and other messages can be sent from the API client to TWS. There is the
            # possibility that function calls made prior to this time could be dropped by TWS.
            self._is_connected = True

            log.info("HistoryApp connected.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="downloads IB data")
    parser.add_argument("--log", default="INFO", choices=["DEBUG", "INFO", "ERROR"])
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log))

    app = HistoryApp()
    app.connect("127.0.0.1", 7496, 721)

    app.run()