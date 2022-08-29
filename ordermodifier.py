import asyncio
from fileinput import close
from binance import AsyncClient, BinanceSocketManager, Client
import config
import json
import urllib.parse
from app import order, round_down
from binance.enums import *


client = Client(config.API_KEY, config.API_SECRET, testnet=True)


class myBinanceSocketManager(BinanceSocketManager):
    def futures_user_socket(self):
        return self._get_account_socket('futures', stream_url=self.FSTREAM_URL if not self.testnet else self.FSTREAM_TESTNET_URL)


def cancel_orders(symbol, OrderId_prefix):
    origClientOrderIdList = json.dumps([OrderId_prefix +
                                        "_S", OrderId_prefix+"_O", OrderId_prefix+"_T"]).replace(" ", "")
    origClientOrderIdList = urllib.parse.quote(origClientOrderIdList)
    return client.futures_cancel_orders(
        symbol=symbol, origClientOrderIdList=origClientOrderIdList)


async def main():
    client_async = await AsyncClient.create(
        config.API_KEY, config.API_SECRET, testnet=True)
    print(client_async)
    # bm = my_BinanceSocketManager(client_async)
    bm = myBinanceSocketManager(client_async)
    # start any sockets here, i.e a trade socket
    ts = bm.futures_user_socket()
    # ts = bm.trade_socket('BNBBTC')
    print("ts = ", ts)
    # then start receiving messages
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            if res['e'] == 'ORDER_TRADE_UPDATE':
                print("res = ", (res))
                symbol = res['o']['s']
                ticksize = 1 if symbol == "BTCUSDT" else 2
                stepsize = 3
                execution_response = "Initialize."
                origOrderId = res['o']['c']
                if res['o']['X'] == 'FILLED':
                    if origOrderId != None and '_F' not in origOrderId:
                        if '_O' in origOrderId:
                            origClientOrderId = origOrderId.replace('_O', '_S')
                            try:
                                SL = client.futures_get_order(
                                    symbol=symbol, origClientOrderId=origClientOrderId)
                            except:
                                client.futures_cancel_all_open_orders(
                                    symbol=symbol)
                                total_position = abs(float(client.futures_position_information(
                                    symbol=symbol)[0]["positionAmt"]))
                                _orderId_tmp = f"OrderModErr_qty_{total_position}"
                                close_params = {"_side": res['o']['S'], "_quantity": total_position, "_symbol": symbol, "_OrderId": _orderId_tmp,
                                                "_order_type": FUTURE_ORDER_TYPE_MARKET}
                                print("execution response = ",
                                      order(**close_params))
                                continue
                            client.futures_cancel_order(
                                symbol=symbol, origClientOrderId=origClientOrderId)
                            order_params = {"_side": SL["side"], "_quantity": round_down(SL["origQty"] - res['o']['q'], stepsize), "_symbol": symbol, "_OrderId": origClientOrderId,
                                            "_price": round_down(SL["price"], ticksize), "_stopPrice": round_down(SL["stopPrice"], ticksize), "_order_type": FUTURE_ORDER_TYPE_STOP}
                            execution_response = order(**order_params)
                        elif '_T' in origOrderId:
                            execution_response = client.futures_cancel_order(
                                symbol=symbol, origClientOrderId=origOrderId.replace('_T', '_S'))
                        elif '_S' in origOrderId:
                            execution_response = cancel_orders(
                                symbol, origOrderId.replace('_S', ''))
                        else:
                            execution_response = "Something went wrong!!!"
                # elif res['o']['X'] == 'CANCELED':
                #     if '_S' in origOrderId:
                #         print(origOrderId)
                #         origQuantity = res['o']['q']
                #         print(cancel_orders(
                #             symbol, origOrderId.replace('_S', '')))
                #         close_params = {"_side": res['o']['S'], "_quantity": origQuantity, "_symbol": symbol, "_OrderId": "Cancelled_Close_All",
                #                         "_order_type": FUTURE_ORDER_TYPE_MARKET}
                #         execution_response = order(**close_params)
                #     elif '_O' in origOrderId or '_T' in origOrderId:
                #         origOrderId = origOrderId.replace(
                #             '_O' if '_O' in origOrderId else '_T', '')
                #         sybling_S = 0
                #         sybling_OT = 0
                #         try:
                #             sybling_S = client.futures_get_order(
                #                 symbol=symbol, origClientOrderId=origOrderId + '_S')
                #         except:
                #             try:
                #                 sybling_OT = client.futures_get_order(
                #                     symbol=symbol, origClientOrderId=origOrderId + ('_T' if '_O' in origOrderId else '_O'))
                #             except:
                #                 print(
                #                     "Order got cancelled but can't get other orders.")
                #                 continue
                #         if sybling_S:
                #             close_params = {"_side": res['o']['S'], "_quantity": sybling_S["origQty"], "_symbol": symbol, "_OrderId": "Cancelled_Close_All",
                #                             "_order_type": FUTURE_ORDER_TYPE_MARKET}
                #             execution_response = order(
                #                 **close_params)
                #         elif sybling_OT:
                #             close_params = {"_side": res['o']['S'], "_quantity": round(sybling_S["origQty"] + res['o']['q'], 3), "_symbol": symbol, "_OrderId": "Cancelled_Close_All",
                #                             "_order_type": FUTURE_ORDER_TYPE_MARKET}
                #             execution_response = order(
                #                 **close_params)
                print("execution_response = ", execution_response)

    await client_async.close_connection()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
