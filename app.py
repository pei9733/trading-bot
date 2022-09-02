from pymongo import MongoClient
import asyncio
import json
import config
from flask import Flask, request, jsonify, render_template
from binance.client import AsyncClient, Client
from binance import BinanceSocketManager
from binance.enums import *
import decimal
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
import time
# from flask_socketio import SocketIO, emit
import urllib.parse


def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        d = decimal.Decimal(value)
        ctx.rounding = decimal.ROUND_DOWN
        return round(d, decimals)


app = Flask(__name__)
# socketio = SocketIO(app)

client = Client(config.API_KEY, config.API_SECRET, testnet=True)


app.config['MONGO_URI'] = config.MONGO_URL
client_mongo = MongoClient(config.MONGO_URL)
db = client_mongo.get_database('myBinanceBot')
db_bar_index = db.bar_index


def order(_side="", _quantity=0.0, _symbol="", _OrderId="", _price=0.0, _stopPrice=0.0, _order_type=FUTURE_ORDER_TYPE_LIMIT,):
    try:
        print(f"sending order {_order_type} - {_side} {_quantity} {_symbol}")
        if _order_type == FUTURE_ORDER_TYPE_LIMIT:
            order = client.futures_create_order(
                symbol=_symbol, side=_side, type=_order_type, price=_price, quantity=_quantity, newClientOrderId=_OrderId, timeInForce='GTC')
        elif _order_type == FUTURE_ORDER_TYPE_MARKET:
            order = client.futures_create_order(
                symbol=_symbol, side=_side, type=_order_type, quantity=_quantity, newClientOrderId=_OrderId)
        else:
            order = client.futures_create_order(
                symbol=_symbol, side=_side, type=_order_type, price=_price, quantity=_quantity, newClientOrderId=_OrderId, stopPrice=_stopPrice, priceProtect=True)
        # elif _order_type == FUTURE_ORDER_TYPE_STOP:
        #     order = client.futures_create_order(
        #         symbol=_symbol, side=_side, type=_order_type, price=_price, quantity=_quantity, newClientOrderId=_OrderId, stopPrice=_stopPrice)
        # elif _order_type == FUTURE_ORDER_TYPE_TAKE_PROFIT:
        #     order = client.futures_create_order(
        #         symbol=_symbol, side=_side, type=_order_type, price=_price, quantity=_quantity, newClientOrderId=_OrderId, stopPrice=_stopPrice)

    except Exception as e:
        print("an exception occured - {}".format(e))
        # print(str(e))
        # if "=-2021)" in str(e):
        #     return [False, "㊣"]
        return [False, _OrderId, e]

    return [True, order, False]


def cancel_order(_symbol, _origOrderId):
    try:
        print(f"canceling order {_symbol} - {_origOrderId}")
        cancel_order = client.futures_cancel_order(
            symbol=_symbol, origClientOrderId=_origOrderId)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return [False, _origOrderId]
    return [True, cancel_order]


@app.route('/')
def welcome():
    return render_template('index.html')

# max algo order num


@app.route('/test', methods=['POST'])
def test():
    # return client.futures_ticker(symbol="BTCUSDT")['lastPrice']  # last price
    # return client.futures_position_information(symbol="BTCUSDT")  # last price
    # test_params = {"_side": "SELL", "_quantity": 0.001, "_symbol": "BTCUSDT", "_OrderId": "L_123456789_TEST",
    #                "_order_type": FUTURE_ORDER_TYPE_MARKET}
    # order(**test_params)
    # return json.dumps(order(**test_params))
    # return json.dumps(client.futures_get_open_orders(symbol="BTCUSDT"))
    # print(client)
    # return
    # start = time.time()
    # orders = client.futures_get_open_orders(symbol="BTCUSDT")
    # order_uuids = []
    # for i in orders:
    #     i_uuid = i['clientOrderId'][:-2]
    #     if not (i_uuid in order_uuids):
    #         order_uuids.append(i_uuid)
    # # client.futures_stream_close()
    # end = time.time()
    # return json.dumps({"time": end - start})
    # return client.futures_get_open_orders(symbol="BTCUSDT")
    # return client.futures_get_order(symbol="BTCUSDT", origClientOrderId="justfortest")
    # return client.futures_exchange_info()     # filter
    # return client.futures_get_order(
    #     symbol="BTCUSDT", origClientOrderId="notexist")
    # return client.futures_cancel_all_open_orders(symbol="BTCUSDT")
    # return client.futures_account()['assets'][1]['walletBalance']
    # for i in client.futures_get_all_orders(symbol="BTCUSDT"):
    #     print(i["clientOrderId"])
    # return False
    OrderId = "L"
    # order_uuid = str(uuid.uuid1().hex)
    order_uuid = "nevergonna"
    # order_uuid = "2af4d149291511ed82cf40ec99c99f2c"
    origClientOrderIdList = json.dumps([OrderId+"_"+order_uuid+"_F", OrderId+"_"+order_uuid +
                                        "_S", OrderId+"_"+order_uuid+"_O", OrderId+"_"+order_uuid+"_T"]).replace(" ", "")
    origClientOrderIdList = urllib.parse.quote(origClientOrderIdList)
    return json.dumps(client.futures_cancel_orders(
        symbol="BTCUSDT", origClientOrderIdList=origClientOrderIdList))

    requestedFutures = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DYDXUSDT']
    print(
        {si['symbol']: si['quantityPrecision']
            for si in info['symbols'] if si['symbol'] in requestedFutures}
    )
    return "OK"


@app.route('/test2', methods=['POST'])
def test2():
    # return json.dumps(client.futures_get_open_orders(symbol="BTCUSDT"))
    # print('0' == client.futures_get_order(symbol="BTCUSDT",
    #       origClientOrderId="L_8bf2179126e611edb0c840ec99c99f2c_S")["executedQty"])
    # print(0 == client.futures_get_order(symbol="BTCUSDT",
    #       origClientOrderId="L_8bf2179126e611edb0c840ec99c99f2c_S")["executedQty"])
    # return json.dumps(client.futures_get_all_orders(symbol="BTCUSDT"))
    # return client.futures_cancel_all_open_orders(symbol="BTCUSDT")
    # return client.futures_get_order(symbol="BTCUSDT", origClientOrderId="web_aByVVd33TXPtH5IbckJW")
    # return client.futures_change_margin_type(symbol="BTCUSDT", marginType="ISOLATED")
    return client.futures_change_leverage(symbol="BTCUSDT", leverage=10)
    # return client.futures_change_leverage(symbol="ETHUSDT", leverage=10)
    lp = float(client.futures_ticker(symbol="BTCUSDT")['lastPrice'])
    # for i in range(5):
    #     print(i)
    order_params_SL = {"_side": "BUY", "_quantity": 0.002, "_symbol": "BTCUSDT", "_OrderId": "justfortest",
                       "_price": lp, "_order_type": FUTURE_ORDER_TYPE_LIMIT}

    res = order(**order_params_SL)
    #     if (res[2] and "=-2021" not in str(res[2])) or not res[2]:
    #         break
    #     # time.sleep(1)
    return json.dumps(res[:2])


@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)
    myOrderType = data['strategy']['alert_message']['orderType']
    symbol = data['ticker'].replace('PERP', '')
    ticksize = 1 if symbol == "BTCUSDT" else 2
    step_round = "{:.3f}"
    side = data['strategy']['order_action'].upper()
    total_position = float(client.futures_position_information(
        symbol=symbol)[0]["positionAmt"])

    if (total_position > 0 and side == "SELL") or (total_position < 0 and side == "BUY"):
        orderid_tmp = "xLbyShort" if total_position > 0 else "xSbyLong"
        client.futures_cancel_all_open_orders(symbol=symbol)
        total_position = float(client.futures_position_information(
            symbol=symbol)[0]["positionAmt"])
        order_params_close_all = {"_side": "SELL" if total_position > 0 else "BUY", "_quantity": abs(total_position), "_symbol": symbol, "_OrderId": orderid_tmp,
                                  "_order_type": FUTURE_ORDER_TYPE_MARKET}
        close_order = order(**order_params_close_all)
    price_mod = (10.0 if side == "BUY" else (-10.0)
                 ) if symbol == "BTCUSDT" else (3.0 if side == "BUY" else (-3.0))
    order_response_PO = False
    order_response_SL = False
    order_response_TP1 = False
    order_response_TP2 = False
    order_uuid = str(uuid.uuid1().hex)
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        print("\n\nPassPhrase Prb\n\n")
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }
    elif myOrderType != 'PLACE_ORDER':
        print("\n\n Not PLACE_ORDER \n\n")
        return {
            "code": "error",
            "message": "NA"
        }
    # elif myOrderType = "CHANGE_SIDE":

    # ———————————————————————————[variables]————————————————————————————————————
    else:
        print("\n\nPLACE_ORDER\n\n")
        OrderId = data['strategy']['alert_message']["order_id"].upper()
        risk = 0.02
        SL = 0.0
        TP1 = 0.0
        TP2 = 0.0
        # return data

        initial_capital = float(client.futures_account()[
                                'assets'][1]['walletBalance'])
        oppsite_side = "BUY" if side == "SELL" else "SELL"
        SL_diff = float(data['strategy']['alert_message']['SL_diff'])
        last_price = float(client.futures_ticker(
            symbol=symbol)['lastPrice'])
        # OrderId = data['strategy']['alert_message']['OrderId'].upper()
        # quantity = float(round_down(initial_capital / last_price if (initial_capital * risk / SL_diff * last_price >
        #                                                              initial_capital) else initial_capital * risk / SL_diff, stepsize))
        halfQty = float(step_round.format((initial_capital / last_price) / 2 if (initial_capital * risk / SL_diff * last_price >
                                                                                 initial_capital) else (initial_capital * risk / SL_diff) / 2))
        quantity = float(step_round.format(halfQty + halfQty))
        # halfQty_1 = float("0."+(int(str(quantity)[2:]) / 2).replace(".", ""))
        # halfQty_1 = float(round_down(quantity / 2.0, stepsize))
        # halfQty_2 = float(round_down(quantity - halfQty_1, stepsize))
        # halfQty_2 = halfQty_2 if halfQty_1 + halfQty_2 == quantity else float(round_down(
        #     halfQty_2 + float(round_down(quantity - halfQty_1 - halfQty_2, stepsize)), stepsize))
    # ——————————————————————————————[End]———————————————————————————————————————
        if side == "BUY":
            SL = round(last_price - SL_diff, ticksize)
            TP1 = round(last_price + SL_diff, ticksize)
            TP2 = round(last_price + SL_diff * 2.0, ticksize)
            SL_stop_price = round(SL + SL_diff * 0.05, ticksize)
            TP1_stop_price = round(TP1 - SL_diff * 0.05, ticksize)
            TP2_stop_price = round(TP2 - SL_diff * 0.05, ticksize)
        else:
            SL = round(last_price + SL_diff, ticksize)
            TP1 = round(last_price - SL_diff, ticksize)
            TP2 = round(last_price - SL_diff * 2.0, ticksize)
            SL_stop_price = round(SL - SL_diff * 0.05, ticksize)
            TP1_stop_price = round(TP1 + SL_diff * 0.05, ticksize)
            TP2_stop_price = round(TP2 + SL_diff * 0.05, ticksize)
        order_params_PO = {"_side": side, "_quantity": quantity, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid + '_F',
                           "_price": last_price + price_mod, "_order_type": FUTURE_ORDER_TYPE_LIMIT}
        order_response_PO = order(**order_params_PO)
        order_params_SL = {"_side": oppsite_side, "_quantity": quantity, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_S',
                           "_price": SL, "_stopPrice": SL_stop_price, "_order_type": FUTURE_ORDER_TYPE_STOP}
        order_params_TP1 = {"_side": oppsite_side, "_quantity": halfQty, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_O',
                            "_price": TP1, "_stopPrice": TP1_stop_price, "_order_type": FUTURE_ORDER_TYPE_TAKE_PROFIT}
        order_params_TP2 = {"_side": oppsite_side, "_quantity": halfQty, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_T',
                            "_price": TP2, "_stopPrice": TP2_stop_price, "_order_type": FUTURE_ORDER_TYPE_TAKE_PROFIT}
        for i in range(5):
            order_response_TP2 = order(**order_params_TP2)
            if (order_response_TP2[2] and "=-2021" not in str(order_response_TP2[2])) or not order_response_TP2[2]:
                break
            time.sleep(1)
        for i in range(5):
            order_response_TP1 = order(**order_params_TP1)
            if (order_response_TP1[2] and "=-2021" not in str(order_response_TP1[2])) or not order_response_TP1[2]:
                break
            time.sleep(1)
        for i in range(5):
            order_response_SL = order(**order_params_SL)
            if (order_response_SL[2] and "=-2021" not in str(order_response_SL[2])) or not order_response_SL[2]:
                break
            time.sleep(1)
    filled = 0
    # print(OrderId+'_'+order_uuid + '_F')
    while filled < 6 and order_response_SL[0] and order_response_TP1[0] and order_response_TP2[0]:
        if client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+'_'+order_uuid + '_F')["status"] == "FILLED":
            break
        print(
            f"Limit order hasn't been filled yet.Wait for 10 sec. {filled * 10} sec")
        filled += 1
        time.sleep(10)
    if filled == 6 and client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+'_'+order_uuid + '_F')["status"] != "FILLED":
        order_response_PO[0] = False
    if order_response_PO[0] and order_response_SL[0] and order_response_TP1[0] and order_response_TP2[0]:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")
        origClientOrderIdList = json.dumps([OrderId+"_"+order_uuid+"_F", OrderId+"_"+order_uuid +
                                            "_S", OrderId+"_"+order_uuid+"_O", OrderId+"_"+order_uuid+"_T"]).replace(" ", "")
        origClientOrderIdList = urllib.parse.quote(origClientOrderIdList)
        client.futures_cancel_orders(
            symbol=symbol, origClientOrderIdList=origClientOrderIdList)
        theorder = client.futures_get_order(
            symbol=symbol, origClientOrderId=OrderId+"_"+order_uuid+"_F")
        position2close = abs(float(theorder["executedQty"]))
        side2close = theorder["side"]
        print(position2close)
        close_order = [True, "position = 0"]
        if position2close != '0':
            _orderId_tmp = f"ErrorClose_qty_{position2close}"
            print(_orderId_tmp)
            order_params_close_all = {"_side": "SELL" if side2close == "BUY" else "BUY", "_quantity": position2close, "_symbol": symbol, "_OrderId": _orderId_tmp,
                                      "_order_type": FUTURE_ORDER_TYPE_MARKET}
            close_order = order(**order_params_close_all)
        return {
            "code": "error",
            "message": "order failed",
            "close_order_response": close_order[1]
        }
