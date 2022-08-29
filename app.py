from email.quoprimime import quote
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


def isProfitTaken():
    """ Function for test purposes. """
    print(client.futures_get_open_orders(symbol="BTCUSDT"))


sched = BackgroundScheduler(daemon=True)
sched.add_job(isProfitTaken, 'interval', seconds=10)
# sched.start()


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
        return [False, _OrderId]

    return [True, order]


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
    return client.futures_exchange_info()     # filter
    return client.futures_get_order(
        symbol="BTCUSDT", origClientOrderId="notexist")
    # return client.futures_cancel_all_open_orders(symbol="BTCUSDT")
    # return client.futures_account()['assets'][1]['walletBalance']
    # for i in client.futures_get_all_orders(symbol="BTCUSDT"):
    #     print(i["clientOrderId"])
    # return False
    OrderId = "L"
    order_uuid = str(uuid.uuid1().hex)
    # , OrderId+"_"+order_uuid +
    origClientOrderIdList = [OrderId+"_"+order_uuid]
    #  "_S", OrderId+"_"+order_uuid+"_1", OrderId+"_"+order_uuid+"_2"]
    return client.futures_cancel_orders(
        symbol="BTCUSDT", origClientOrderIdList=origClientOrderIdList)

    requestedFutures = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DYDXUSDT']
    print(
        {si['symbol']: si['quantityPrecision']
            for si in info['symbols'] if si['symbol'] in requestedFutures}
    )
    return "OK"


@app.route('/test2', methods=['POST'])
def test2():
    # return json.dumps(client.futures_get_open_orders(symbol="BTCUSDT"))
    return json.dumps(client.futures_get_all_orders(symbol="BTCUSDT"))
    return client.futures_cancel_all_open_orders(symbol="BTCUSDT")
    data = json.loads(request.data)
    return data


@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)
    myOrderType = data['strategy']['alert_message']['orderType']
    symbol = data['ticker'].replace('PERP', '')
    ticksize = 1 if symbol == "BTCUSDT" else 2
    stepsize = 3
    side = data['strategy']['order_action'].upper()
    total_position = float(client.futures_position_information(
        symbol=symbol)[0]["positionAmt"])
    OrderId = data['strategy']["order_id"].upper()
    if (total_position > 0 and side == "SELL") or (total_position < 0 and side == "BUY"):
        orderid_tmp = "xLbyShort" if total_position > 0 else "xSbyLong"
        client.futures_cancel_all_open_orders(symbol=symbol)
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
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }
    elif myOrderType == "NA":
        return {
            "code": "error",
            "message": "NA"
        }
    # elif myOrderType = "CHANGE_SIDE":

    # ———————————————————————————[variables]————————————————————————————————————
    elif myOrderType == 'PLACE_ORDER':
        risk = 0.02
        SL = 0.0
        TP1 = 0.0
        TP2 = 0.0
        # return data
        last_price = float(client.futures_ticker(
            symbol=symbol)['lastPrice'])
        initial_capital = float(client.futures_account()[
                                'assets'][1]['walletBalance'])
        oppsite_side = "BUY" if side == "SELL" else "SELL"
        SL_diff = float(data['strategy']['alert_message']['SL_diff'])

        # OrderId = data['strategy']['alert_message']['OrderId'].upper()
        quantity = float(round_down(initial_capital / last_price if (initial_capital * risk / SL_diff * last_price >
                                                                     initial_capital) else initial_capital * risk / SL_diff, stepsize))
        halfQty = float(round_down(quantity * 0.5, stepsize))
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
        order_params_TP2 = {"_side": oppsite_side, "_quantity": quantity - halfQty, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_T',
                            "_price": TP2, "_stopPrice": TP2_stop_price, "_order_type": FUTURE_ORDER_TYPE_TAKE_PROFIT}
        order_response_SL = order(**order_params_SL)
        order_response_TP1 = order(**order_params_TP1)
        order_response_TP2 = order(**order_params_TP2)
        # order_response = order(side, quantity, symbol,
        #                        OrderId, last_price + price_mod, FUTURE_ORDER_TYPE_LIMIT,)
        # order_response2 = order(oppsite_side, quantity, symbol,
        #                         OrderId+'_SL', round_down(SL, 1), round_down(SL_stop_price, 1), FUTURE_ORDER_TYPE_STOP)
    # elif myOrderType == 'TAKE_PROFIT1':
    #     origOrderId = data['strategy']['alert_message']['origOrderId'].upper()
    #     origSTOP = client.futures_get_order(
    #         symbol=symbol, origClientOrderId=origOrderId+"_SL")
    #     origQty = float(origSTOP["origQty"])
    #     origStopPrice = float(origSTOP["stopPrice"])
    #     origPrice = float(origSTOP["price"])
    #     cancel_resp = cancel_order(
    #         symbol, origOrderId + "_SL")
    #     last_price = float(client.futures_ticker(
    #         symbol=symbol)['lastPrice']) + price_mod
    #     modQty = float(round_down(origQty * 0.5, 3))
    #     order_params_1 = {"_side": side, "_quantity": modQty, "_symbol": symbol, "_OrderId": origOrderId +
    #                       "_TAKE_PROFIT_1", "_price": last_price, "_order_type": FUTURE_ORDER_TYPE_LIMIT}
    #     order_params_2 = {"_side": side, "_quantity": round_down(origQty - modQty, 3), "_symbol": symbol, "_OrderId": origOrderId+"_SL_TAKE_PROFIT_1",
    #                       "_price": round_down(origPrice, 1), "_stopPrice": round_down(origStopPrice, 1), "_order_type": FUTURE_ORDER_TYPE_STOP}
    #     order_response = order(side, modQty, symbol,
    #                            origOrderId+"_TAKE_PROFIT_1", last_price, FUTURE_ORDER_TYPE_LIMIT,)
    #     order_response2 = order(side, round_down(origQty - modQty, 3), symbol,
    #                             origOrderId+"_SL_TAKE_PROFIT_1", round_down(origPrice, 1), round_down(origStopPrice, 1), FUTURE_ORDER_TYPE_STOP)
    #     if not cancel_resp:
    #         order_response = False
    # elif myOrderType == 'TAKE_PROFIT2':
    #     origOrderId = data['strategy']['alert_message']['origOrderId'].upper()
    #     last_price = float(client.futures_ticker(symbol=symbol)['lastPrice'])
    #     total_position = float(client.futures_position_information(
    #         symbol=symbol)[0]["positionAmt"])
    #     order_params_1 = {"_side": "SELL" if total_position > 0 else "BUY", "_quantity": abs(
    #         total_position), "_symbol": symbol, "_OrderId": origOrderId+"_TAKE_PROFIT_2", "_price": last_price + price_mod, "_order_type": FUTURE_ORDER_TYPE_LIMIT}
    #     order_response2 = cancel_order(
    #         symbol, origOrderId+"_SL_TAKE_PROFIT_1")
    #     order_response = order("SELL" if total_position > 0 else "BUY", abs(total_position),
    #                            symbol, origOrderId+"_TAKE_PROFIT_2", last_price + price_mod, FUTURE_ORDER_TYPE_LIMIT,)
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

        total_position = float(client.futures_position_information(
            symbol=symbol)[0]["positionAmt"])
        close_order = [True, "position = 0"]
        if total_position != 0 and client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+"_"+order_uuid+"_F")["status"] == "FILLED":
            _orderId_tmp = f"ErrorClose_qty_{quantity}"
            print(_orderId_tmp)
            order_params_close_all = {"_side": "SELL" if total_position > 0 else "BUY", "_quantity": quantity, "_symbol": symbol, "_OrderId": _orderId_tmp,
                                      "_order_type": FUTURE_ORDER_TYPE_MARKET}
            close_order = order(**order_params_close_all)
        return {
            "code": "error",
            "message": "order failed",
            "close_order_response": close_order[1]
        }