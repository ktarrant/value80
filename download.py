from collections import OrderedDict
from queue import Queue, Empty
import logging
import datetime

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

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
    _ST_INIT, _ST_DETAILS, _ST_BACKFILL, _ST_CONNECTED, _ST_DISCONNECT = range(5)
    _REQ_DETAILS, _REQ_HISTORY = range(2)

    def __init__(self, contract, live=False):
        HistoryWrapper.__init__(self)
        HistoryClient.__init__(self, wrapper=self)

        self.contract = contract
        self.live = live

        self._state = self._ST_INIT
        self._queue = Queue()

    def yieldAllBars(self):
        while self._state in [self._ST_BACKFILL, self._ST_CONNECTED]:
            # Blocking call to Queue.get() since we are still producing new bars in these states
            bar = self._queue.get(block=True)
            cleaned = self._clean_bar(bar)
            yield cleaned

        # clear out remaining items in queue
        while True:
            try:
                bar = self._queue.get(block=False)
                cleaned = self._clean_bar(bar)
                yield cleaned
            except Empty:
                break


    def _clean_bar(self, bar):
        rv = OrderedDict([("datetime", bar.date)])
        for key in ["high", "low", "open", "close", "volume"]:
            rv[key] = getattr(bar, key)
        return rv

    def nextValidId(self, orderId):
        if self._state == self._ST_INIT:
            # IBApi.EWrapper.nextValidID callback is commonly used to indicate that the connection
            # is completed and other messages can be sent from the API client to TWS. There is the
            # possibility that function calls made prior to this time could be dropped by TWS.
            self._state = self._ST_DETAILS

            log.info("HistoryApp connected.")
            self.reqContractDetails(self._REQ_DETAILS, self.contract)

    def contractDetails(self, reqId, contractDetails):
        if reqId != self._REQ_DETAILS:
            log.error("Unexpected contract details callback: {}".format(contractDetails.summary))
            return

        if self._state == self._ST_DETAILS:
            log.info("Successfully loaded contract details: {}".format(contractDetails.summary))

            self._state = self._ST_BACKFILL
            self.reqHistoricalData(self._REQ_HISTORY,
                                   self.contract,
                                   "", # the empty string indicates the present moment
                                   "1 M",
                                   "30 mins",
                                   "TRADES",
                                   1, 1, False, []
                                   )

    def historicalData(self, reqId, bar):
        if reqId != self._REQ_HISTORY:
            log.error(("Unexpected historical data. " +
                       "{} Date: {} Open: {} High: {} Low: {} Close: " +
                       "{} Volume: {} Count: {} WAP: {}").format(
                        reqId, bar.date, bar.open, bar.high, bar.low, bar.close,
                        bar.volume,bar.barCount, bar.average)
            )

        if self._state == self._ST_BACKFILL:
            self._queue.put(bar)

    def historicalDataEnd(self, reqId, start, end):
        if reqId == self._REQ_HISTORY and self._state == self._ST_BACKFILL:
            log.info("Backfill complete: [{}, {}]".format(start, end))


            if self.live == False:
                self._state = self._ST_DISCONNECT
                self.disconnect()
            else:
                self._state = self._ST_CONNECTED
                # TODO: Implement live data
                raise NotImplementedError("Live data not implemented!")

def get_contract_options():
    es_contract = Contract()
    es_contract.secType = "FUT"
    es_contract.exchange = "GLOBEX"
    es_contract.currency = "USD"
    es_contract.localSymbol = "ESZ7"
    return OrderedDict([
        ("ES", es_contract),
    ])

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="downloads IB data")
    parser.add_argument("--log", default="INFO", choices=["DEBUG", "INFO", "ERROR"])
    contract_options = get_contract_options()
    symbol_options = list(contract_options.keys())
    parser.add_argument("--symbol", default=symbol_options[0], choices=symbol_options)
    args = parser.parse_args()

    # configure logging
    logging.basicConfig(level=getattr(logging, args.log))

    # select contract
    contract = contract_options[args.symbol]

    app = HistoryApp(contract)
    app.connect("127.0.0.1", 7496, 721)

    app.run()

    import pandas as pd
    df = pd.DataFrame(app.yieldAllBars())
    df = df.set_index("datetime")
    print(df)
    df.to_csv("{}.csv".format(args.symbol))