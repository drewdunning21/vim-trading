import bybit
import datetime

class BybitAcct:

    def __init__(self, key, priv):
        self.key = key
        self.priv = priv
        self.client = bybit.bybit(test=False, api_key=self.key, api_secret=self.priv)

    def limitOrder(self, symbol, amnt, price, side, sl: float = 0, tp: float = 0):
        order = None
        if (sl != 0 and tp != 0): order = self.client.Order.Order_new(side=side,symbol=symbol,order_type="Limit",qty=amnt,price=price,time_in_force="GoodTillCancel", stop_loss = sl, take_profit = tp).result()
        else: order = self.client.Order.Order_new(side=side,symbol=symbol,order_type="Limit",qty=amnt,price=price,time_in_force="GoodTillCancel").result()
        self.checkReq(order[0], 'limit order')
        order = order[0]['result']
        rej = order['reject_reason']
        orderId = order['order_id']
        return orderId if rej == 'EC_NoError' else ''

    def marketOrder(self, symbol, amnt, side):
        req = self.client.Order.Order_new(side=side,symbol=symbol,order_type="Market",qty=amnt,price=8300,time_in_force="GoodTillCancel").result()
        self.checkReq(req[0], 'market order')

    def getBook(self, symbol):
        book =  self.client.Market.Market_orderbook(symbol=symbol).result()
        self.checkReq(book[0], 'get book')
        return book

    def getSpread(self, symbol):
        book = self.getBook(symbol)
        spread = {}
        spread['bid'] = book[0]['result'][0]
        spread['ask'] = book[0]['result'][25]
        return spread

    def getStatus(self, symbol, orderId):
        status = self.client.Order.Order_query(symbol=symbol, order_id=orderId).result()
        self.checkReq(status[0], 'get status')
        return status[0]['result']

    def replaceOrder(self, orderId, symbol, price, amnt):
        newId = None
        while not newId:
            order = self.client.Order.Order_replace(symbol=symbol, order_id=orderId, p_r_qty=str(amnt), p_r_price=price).result()
            self.checkReq(order[0], 'replace order')
            order = order[0]['result']
            if order != None:
                newId = order['order_id']
        return newId

    def getPositions(self, symbol):
        pos = (self.client.Positions.Positions_myPosition(symbol=symbol).result())
        self.checkReq(pos[0], 'get positions')
        return pos[0]['result']

    def getPriceData(self, time, period):
        return self.client.Kline.Kline_get(symbol="BTCUSD", interval=time, **{'from':period}).result()[0]

    def getBalance(self, symbol):
        req = self.client.Wallet.Wallet_getBalance(coin=symbol).result()
        if req[0] is None: return req
        if req[0]['result'] is None: return req
        if req[0]['result'][symbol] is None: return req
        self.checkReq(req[0], 'get balance')
        return req[0]['result'][symbol]

    def getTradeHistory(self) -> dict:
        req = self.client.Execution.Execution_getTrades(symbol="BTCUSD").result()
        self.checkReq(req[0], 'trade history')
        return req[0]['result']

    def checkReq(self, req, name: str):
        ct = str(datetime.datetime.now()).split('.')[0]
        # printt('[' + ct + '] ' + name + ' ' + str(req['rate_limit_status']) + ' ' + str(req['ret_code']))
        if req['ret_code'] != 0:
            printt('[' + ct + '] ' + name + ' ' + str(req['ret_code']))
            printt(req)

def printt(txt):
    file = open('./text.txt', 'a')
    file.write(str(txt) + '\n')
    file.close()
