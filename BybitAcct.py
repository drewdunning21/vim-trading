import bybit
import time

class BybitAcct:

    def __init__(self, key, priv):
        self.key = key
        self.priv = priv
        self.client = bybit.bybit(test=False, api_key=self.key, api_secret=self.priv)

    def limitBuy(self, symbol, amnt, price):
# {
#     "ret_code": 0,
#     "ret_msg": "OK",
#     "ext_code": "",
#     "ext_info": "",
#     "result": {
#         "user_id": 1,
#         "order_id": "335fd977-e5a5-4781-b6d0-c772d5bfb95b",
#         "symbol": "BTCUSD",
#         "side": "Buy",
#         "order_type": "Limit",
#         "price": 8800,
#         "qty": 1,
#         "time_in_force": "GoodTillCancel",
#         "order_status": "Created",
#         "last_exec_time": 0,
#         "last_exec_price": 0,
#         "leaves_qty": 1,
#         "cum_exec_qty": 0,
#         "cum_exec_value": 0,
#         "cum_exec_fee": 0,
#         "reject_reason": "",
#         "order_link_id": "",
#         "created_at": "2019-11-30T11:03:43.452Z",
#         "updated_at": "2019-11-30T11:03:43.455Z"
#     },
#     "time_now": "1575111823.458705",
#     "rate_limit_status": 98,
#     "rate_limit_reset_ms": 1580885703683,
#     "rate_limit": 100
# }

        order = self.client.Order.Order_new(side="Buy",symbol=symbol,order_type="Limit",qty=amnt,price=price,time_in_force="GoodTillCancel").result()
        order = order[0]['result']
        rej = order['reject_reason']
        orderId = order['order_id']
        return orderId if rej == 'EC_NoError' else ''

    def limitSell(self, symbol, amnt, price):
        order = self.client.Order.Order_new(side="Sell",symbol=symbol,order_type="Limit",qty=amnt,price=price,time_in_force="GoodTillCancel").result()
        order = order[0]['result']
        rej = order['reject_reason']
        orderId = order['order_id']
        return orderId if rej == 'EC_NoError' else ''

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
        # price = str(price)
        # if '.' in price:
        #     price += '0'
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
        orderId = self.limitBuy(symbol, amnt, bid)
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
        orderId = self.limitSell(symbol, amnt, ask)
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
