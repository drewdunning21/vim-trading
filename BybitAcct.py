import bybit
import time

class BybitAcct:

    def __init__(self, key, priv):
        self.key = key
        self.priv = priv
        self.client = bybit.bybit(test=False, api_key=self.key, api_secret=self.priv)

    def limitOrder(self, symbol, amnt, price, side):
        order = self.client.Order.Order_new(side=side,symbol=symbol,order_type="Limit",qty=amnt,price=price,time_in_force="GoodTillCancel").result()
        order = order[0]['result']
        rej = order['reject_reason']
        orderId = order['order_id']
        return orderId if rej == 'EC_NoError' else ''

    def marketOrder(self, symbol, amnt, side):
        self.client.Order.Order_new(side=side,symbol=symbol,order_type="Market",qty=amnt,price=8300,time_in_force="GoodTillCancel").result()

    def getBook(self, symbol):
        return self.client.Market.Market_orderbook(symbol=symbol).result()

    def getSpread(self, symbol):
        book = self.getBook(symbol)
        spread = {}
        spread['bid'] = book[0]['result'][0]
        spread['ask'] = book[0]['result'][25]
        return spread

    def getStatus(self, symbol, orderId):
        status = self.client.Order.Order_query(symbol=symbol, order_id=orderId).result()[0]['result']['order_status']
        return status

    def replaceOrder(self, orderId, symbol, price, amnt):
        newId = None
        while not newId:
            order = self.client.Order.Order_replace(symbol=symbol, order_id=orderId, p_r_qty=amnt, p_r_price=price).result()
            order = order[0]['result']
            if order != None:
                newId = order['order_id']
        return newId

    def chaseBuy(self, symbol, amnt, maxPrice=1000000000):
        spread = self.getSpread(symbol)
        # make the initial order
        bid = float(spread['bid']['price']) - 5
        orderId = self.limitOrder(symbol, amnt, bid, 'Buy')
        status = ''
        if not orderId:
            print('Order failed')
            return
        while status != 'Filled':
            spread = self.getSpread(symbol)
            newBid = float(spread['bid']['price'])
            # check if price greater than max price
            if newBid > maxPrice:
                return 0
            # if not, check if the cur bid is greater than cur order bid
            if newBid != bid:
                # if so, adjust cur order bid
                orderId = self.replaceOrder(orderId, symbol, str(newBid), str(amnt))
                bid = newBid
            status = self.getStatus(symbol, orderId)
        print('order filled')
        return

    def chaseSell(self, symbol, amnt, minPrice=0):
        spread = self.getSpread(symbol)
        # make the initial order
        ask = float(spread['ask']['price']) + 5
        orderId = self.limitOrder(symbol, amnt, ask, 'Sell')
        status = ''
        if not orderId:
            print('Order failed')
            return
        while status != 'Filled':
            spread = self.getSpread(symbol)
            newAsk = float(spread['ask']['price'])
            # check if price greater than max price
            if newAsk < minPrice:
                return 0
            # if not, check if the cur bid is greater than cur order bid
            if newAsk != ask:
                # if so, adjust cur order bid
                orderId = self.replaceOrder(orderId, symbol, str(newAsk), str(amnt))
                ask = newAsk
            status = self.getStatus(symbol, orderId)
        print('order filled')

    def replaec(self, symbol, orderId):
        self.client.Order.Order_replace(symbol=symbol, order_id=orderId).result()
