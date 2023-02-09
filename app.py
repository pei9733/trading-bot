# 1,756.60706173 9/5 0226
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
from datetime import datetime


def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        d = decimal.Decimal(value)
        ctx.rounding = decimal.ROUND_DOWN
        return round(d, decimals)


app = Flask(__name__)
# socketio = SocketIO(app)

client = Client(config.API_KEY, config.API_SECRET, testnet=True)

ASKSBIDS = ['asks', 'bids']
SIDE = ['BUY', 'SELL']
# app.config['MONGO_URI'] = config.MONGO_URL
# client_mongo = MongoClient(config.MONGO_URL)
# db = client_mongo.get_database('myBinanceBot')
# db_bar_index = db.bar_index

def orderQuery(_symbol, _OrderId):
    try:
        return client.futures_get_order(
            symbol=_symbol, origClientOrderId=_OrderId)
    except:
        print("order Query failed")
        close_order = close_all(_symbol)
def order(_side="", _quantity=0.0, _symbol="", _OrderId="", _price=0.0, _stopPrice=0.0, _order_type=FUTURE_ORDER_TYPE_LIMIT, _tif='GTC'):
    try:
        print(f"sending order {_order_type} - {_side} {_quantity} {_symbol}")
        if _order_type == FUTURE_ORDER_TYPE_LIMIT:
            order = client.futures_create_order(
                symbol=_symbol, side=_side, type=_order_type, price=_price, quantity=_quantity, newClientOrderId=_OrderId, timeInForce=_tif)
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


def close_all(symbol):
    step_round = "{:.3f}"
    client.futures_cancel_all_open_orders(symbol=symbol)
    total_position = float(client.futures_position_information(
        symbol=symbol)[0]["positionAmt"])
    if total_position == 0:
        print("\nCLOSE_ALL BUT NOTHING TO CLOSE\n")
        return [True, "position = 0", True]
    side = "BUY" if total_position < 0 else "SELL"
    total_position = abs(total_position)
    _orderId_tmp = f"ErrCls_qty_{total_position}_exc"
    close_params = {"_side": side, "_quantity": float(step_round.format(total_position)), "_symbol": symbol, "_OrderId": _orderId_tmp,
                    "_order_type": FUTURE_ORDER_TYPE_MARKET}
    return order(**close_params)


@app.route('/')
def welcome():
    return render_template('index.html')

# max algo order num


@app.route('/test', methods=['POST'])
def test():
    # return client.futures_ticker(symbol="BTCUSDT")['lastPrice']  # last price
    # return client.futures_position_information(symbol="BTCUSDT")  # last price
    return(json.dumps(client.futures_order_book(symbol="BTCUSDT", limit=5)['asks'][0]))

    # data = json.loads(request.data)
    # size = data['strategy']['position_size']
    test_params = {"_side": "SELL", "_quantity": 0.001, "_symbol": "BTCUSDT", "_OrderId": "L_TEST",
                   "_order_type": FUTURE_ORDER_TYPE_MARKET}
    return json.dumps(client.futures_account()[
        'assets'][3]['walletBalance'])
    order(**test_params)

    return json.dumps(order(**test_params))
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
    # return (client.futures_position_information(
    #     symbol="BTCUSDT")[0]["positionAmt"])
    # return json.dumps(client.futures_get_open_orders(symbol="BTCUSDT"))
    # return (client.futures_get_order(symbol="BTCUSDT",
    #  origClientOrderId="L_TEST_TP1"))
    # print(type(client.futures_get_order(symbol="BTCUSDT",
    #       origClientOrderId="L_8bf2179126e611edb0c840ec99c99f2c_S")["time"]))
    # return json.dumps(cancel_order("BTCUSDT", "L_0b20bc4f29c411eda43b40ec99c99f2c_T"))

    list_ = client.futures_get_all_orders(symbol="BTCUSDT")
    print(datetime.fromtimestamp(int(list_[0]['time']/1000)))
    for i in list_:
        i["time"] = str(datetime.fromtimestamp(i["time"]/1000))[:19]
        i["updateTime"] = str(
            datetime.fromtimestamp(i["updateTime"]/1000))[:19]
    return json.dumps(list_)
    return client.futures_cancel_all_open_orders(symbol="BTCUSDT")
    # return client.futures_get_order(symbol="BTCUSDT", origClientOrderId="web_aByVVd33TXPtH5IbckJW")
    # return client.futures_change_margin_type(symbol="BTCUSDT", marginType="ISOLATED")
    try:
        data = json.loads(request.data)
    except:
        return json.dumps(["Weird"])
    try:
        return data['fdsfadsafdaf']
    except:
        return "fuck u"

    # tot = abs(float(client.futures_position_information(
    #     symbol="BTCUSDT")[0]["positionAmt"]))
    # if tot == 0:
    #     print(True)
    # else:
    #     print(False)
    # return client.futures_change_leverage(symbol="BTCUSDT", leverage=10)
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

# // orderType 0 denotes NA
# // orderType 1 denotes place_order
# // orderType 2, 3 denotes TP1, TP2
# // orderType 4 denotes stop loss
# // orderType 5 denotes change side
@app.route('/webhook', methods=['POST'])  # if PO is not executed completely?
def webhook():
    try:
        data = json.loads(request.data)
    except:
        return json.dumps(["Decline"])
    try:
        if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
            print("\n\nPassPhrase Prb\n\n")
            return {
                "code": "error",
                "message": "Invalid passphrase"
            }
    except:
        return json.dumps(["Decline"])
    OrderId = data['strategy']['alert_message']["origOrderId"].upper()
    orderType = data['strategy']['alert_message']['orderType']
    symbol = data['ticker'].replace('PERP', '')
    ticksize = 1 if symbol == "BTCUSDT" else 2
    step_round = "{:.3f}"
    side = 0 if data['strategy']['order_action'].upper() == "BUY" else 1    # 0 == buy; 1 == sell
    asksbids = 0 if side == 1 else 1
    total_position = float(client.futures_position_information(
        symbol=symbol)[0]["positionAmt"])
    price_mod = (10.0 if side == 0 else (-10.0)
                 ) if symbol == "BTCUSDT" else (3.0 if side == 0 else (-3.0))
    order_response = True
    # order_response_SL = [True, True, False]
    # order_response_TP1 = [True, True, False]
    # order_response_TP2 = [True, True, False]
    # order_uuid = str(uuid.uuid1().hex)
    if orderType == '2':
        origOrder = orderQuery(symbol, OrderId)
        last_price = float(client.futures_ticker(symbol=symbol)['lastPrice'])
        order_params = {"_side": SIDE[side], "_quantity": float(step_round.format(float(origOrder["executedQty"]) / 2.0)), "_symbol": symbol, "_OrderId": OrderId + "_2",
                        "_price": round_down(float(last_price), ticksize), "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif":"IOC"}
        for i in range(3):  # 這是一定要掛不是一定要賣
            execution_response = order(**order_params)
            if (execution_response[2] and "=-2021" not in str(execution_response[2])) or not execution_response[2]:
                break
            time.sleep(1)
        if not execution_response[0]:
            order_params = {"_side": SIDE[side], "_quantity": float(step_round.format(float(origOrder["executedQty"]) / 2.0)), "_symbol": symbol, "_OrderId": OrderId + "_TP1_M",
                            "_order_type": FUTURE_ORDER_TYPE_MARKET}
            execution_response = order(**order_params)
    elif orderType == '3':
        try:
            origOrder = client.futures_get_order(
                symbol=symbol, origClientOrderId=OrderId)
        except:
            print("order Query failed")
            close_order = close_all(symbol)
            return {
                "code": "error",
                "message": "order Query failed",
                "close_order_response": close_order[1]
            }
        try:
            order_TP1 = client.futures_get_order(
                symbol=symbol, origClientOrderId=OrderId + '_TP1')
        except:
            try:
                order_TP1 = client.futures_get_order(
                    symbol=symbol, origClientOrderId=OrderId + '_TP1_M')
            except:
                print("order Query failed")
                close_order = close_all(symbol)
                return {
                    "code": "error",
                    "message": "order Query failed",
                    "close_order_response": close_order[1]
                }

    elif orderType == '0':
        print("\n\n Not PLACE_ORDER \n\n")
        return {
            "code": "error",
            "message": "NA"
        }
    # elif orderType = "CHANGE_SIDE":

    # ———————————————————————————[variables]————————————————————————————————————
    elif orderType == '1':   # place order's orderID : L_{timestamp}_1  /  S_{timestamp}_1
        if (total_position > 0 and side == 1) or (total_position < 0 and side == 0):
            print("\n\nCHANGE SIDE\n\n")
            orderid_tmp = "xLbyShort" if total_position > 0 else "xSbyLong"
            client.futures_cancel_all_open_orders(symbol=symbol)
            total_position = float(client.futures_position_information(
                symbol=symbol)[0]["positionAmt"])
            order_params_close_all = {"_side": "SELL" if total_position > 0 else "BUY", "_quantity": abs(total_position), "_symbol": symbol, "_OrderId": orderid_tmp,
                                      "_order_type": FUTURE_ORDER_TYPE_MARKET}
            close_order = order(**order_params_close_all)
        print("\n\nPLACE_ORDER\n\n")
        risk = 0.01
        SL = 0.0
        TP1 = 0.0
        TP2 = 0.0
        # return data

        initial_capital = float(client.futures_account()[
                                'assets'][3]['walletBalance'])
        SL_diff = float(data['strategy']['alert_message']['SL_diff'])
        qty_price = float(str(data['strategy']['order_price'])[:7])
        last_price = float(client.futures_ticker(
            symbol=symbol)['lastPrice'])
        # OrderId = data['strategy']['alert_message']['OrderId'].upper()
        # quantity = float(round_down(initial_capital / last_price if (initial_capital * risk / SL_diff * last_price >
        #                                                              initial_capital) else initial_capital * risk / SL_diff, stepsize))
        halfQty = float(step_round.format((initial_capital / qty_price) / 2 if (initial_capital * risk / SL_diff * qty_price >
                                                                                initial_capital) else (initial_capital * risk / SL_diff) / 2))
        quantity = float(step_round.format(halfQty + halfQty))
        # halfQty_1 = float("0."+(int(str(quantity)[2:]) / 2).replace(".", ""))
        # halfQty_1 = float(round_down(quantity / 2.0, stepsize))
        # halfQty_2 = float(round_down(quantity - halfQty_1, stepsize))
        # halfQty_2 = halfQty_2 if halfQty_1 + halfQty_2 == quantity else float(round_down(
        #     halfQty_2 + float(round_down(quantity - halfQty_1 - halfQty_2, stepsize)), stepsize))
    # ——————————————————————————————[End]———————————————————————————————————————
        if side == 0:
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
        # order_params_1 = {"_side": side, "_quantity": quantity, "_symbol": symbol, "_OrderId": OrderId+'_1',   # First
        #                    "_price": last_price + price_mod, "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif": "IOC"}
        filled = 0
        while filled < 20:
            filled += 1
            if filled == 10:
                asksbids = not asksbids
            order_price = float(client.futures_order_book(
                symbol=symbol, limit=5)[ASKSBIDS[asksbids]][0][0]) 
            slip_effi = 0.02
            if abs(order_price - qty_price) / qty_price > slip_effi:
                continue
            order_params_1 = {"_side": SIDE[side], "_quantity": quantity, "_symbol": symbol, "_OrderId": OrderId+'_1',   # First
                               "_price": order_price, "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif": "IOC"}
            order_response = order(**order_params_1)
            time.sleep(0.5)
            if client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+'_1')['status'] == 'FILLED':
                print(client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+'_1')['avgPrice'])
                print(filled)
                break
            
        

        # order_params_SL = {"_side": oppsite_side, "_quantity": quantity, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_S',  # Stop Loss
        #                    "_price": SL, "_stopPrice": SL_stop_price, "_order_type": FUTURE_ORDER_TYPE_STOP}
        # order_params_TP1 = {"_side": oppsite_side, "_quantity": halfQty, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_O',  # One
        #                     "_price": TP1, "_stopPrice": TP1_stop_price, "_order_type": FUTURE_ORDER_TYPE_TAKE_PROFIT}
        # order_params_TP2 = {"_side": oppsite_side, "_quantity": halfQty, "_symbol": symbol, "_OrderId": OrderId+'_'+order_uuid+'_T',  # Two
        #                     "_price": TP2, "_stopPrice": TP2_stop_price, "_order_type": FUTURE_ORDER_TYPE_TAKE_PROFIT}

        # filled = 0
        # # print(OrderId+'_'+order_uuid + '_F')
        # while filled < 12:
        #     if client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+'_'+order_uuid + '_F')["status"] == "FILLED":
        #         break
        #     print(
        #         f"Limit order hasn't been filled yet.Wait for 5 sec. {filled * 5} sec")
        #     filled += 1
        #     time.sleep(5)
        # if filled != 12 or client.futures_get_order(symbol=symbol, origClientOrderId=OrderId+'_'+order_uuid + '_F')["status"] == "FILLED":
        #     order_response_PO[0] = True
        #     for i in range(5):
        #         order_response_SL = order(**order_params_SL)
        #         if (order_response_SL[2] and "=-2021" not in str(order_response_SL[2])) or not order_response_SL[2]:
        #             break
        #         time.sleep(1)
        #     if order_response_SL[0]:
        #         for i in range(5):
        #             order_response_TP1 = order(**order_params_TP1)
        #             if (order_response_TP1[2] and "=-2021" not in str(order_response_TP1[2])) or not order_response_TP1[2]:
        #                 break
        #             time.sleep(1)
        #     if order_response_SL[0] and order_response_TP1[0]:
        #         for i in range(5):
        #             order_response_TP2 = order(**order_params_TP2)
        #             if (order_response_TP2[2] and "=-2021" not in str(order_response_TP2[2])) or not order_response_TP2[2]:
        #                 break
        #             time.sleep(1)

    if order_response:
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
            _orderId_tmp = f"ErrCls_qty_{position2close}_exc"
            print(_orderId_tmp)
            order_params_close_all = {"_side": "SELL" if side2close == "BUY" else "BUY", "_quantity": position2close, "_symbol": symbol, "_OrderId": _orderId_tmp,
                                      "_order_type": FUTURE_ORDER_TYPE_MARKET}
            close_order = order(**order_params_close_all)
        return {
            "code": "error",
            "message": "order failed",
            "close_order_response": close_order[1]
        }
