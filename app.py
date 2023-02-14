#2023/2/14 14:20 1437.738USDT
import asyncio
import json
import config
from flask import Flask, request, jsonify, render_template
from binance.client import AsyncClient, Client
from binance import BinanceSocketManager
from binance.enums import *
import decimal
from apscheduler.schedulers.background import BackgroundScheduler
import time
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
SIDE = ['BUY', 'SELL']  # buy = 0, sell = 1
step_round = "{:.3f}"
slip_effi = 0.02
# app.config['MONGO_URI'] = config.MONGO_URL
# client_mongo = MongoClient(config.MONGO_URL)
# db = client_mongo.get_database('myBinanceBot')
# db_bar_index = db.bar_index

def orderQuery(_symbol, _OrderId, _ignore = False, _message = ""):
    try:
        return client.futures_get_order(
            symbol=_symbol, origClientOrderId=_OrderId)
    except Exception as e:
        print(_message)
        if '2013' in str(e):
            if _ignore:
                return False
            print(f"order {_OrderId} does not exist")
        else:
            print("order Query failed")
            close_order = close_all(_symbol)
            return False
def ordersQuery(_symbol, _OrderId,_exist = False, _message = ""): # _exist = True if only wants to check whether the order is existed
    index = 0
    executedQty = 0
    origOrder = True
    while origOrder and index < 20:
        index += 1 
        origOrder = orderQuery(_symbol, _OrderId + f'_{index}', True, _message)
        if origOrder:
            executedQty += float(origOrder['executedQty'])
            if _exist:
                return True
    marketOrder = orderQuery(_symbol, _OrderId + '_M', True, _message)
    if marketOrder:
        executedQty += float(marketOrder['executedQty'])
        if _exist:
            return True
    return float(step_round.format(executedQty))
def order(_side="", _quantity=0.0, _symbol="", _OrderId="", _price=0, _tv_price = 0.0, _stopPrice=0.0, _order_type=FUTURE_ORDER_TYPE_LIMIT, _tif='GTC', _asksbids = 0, _force = False, _reduceOnly = False):
    try:
        print(f"sending order {_order_type} - {_side} {_quantity} {_symbol}")
        filled = 0
        executedQty = 0.0
        while filled < 20:
            filled += 1
            orderID = _OrderId+f'_{filled}'
            if filled == 10:
                _asksbids = not _asksbids
            order_price = float(client.futures_order_book(
                symbol=_symbol, limit=5)[ASKSBIDS[_asksbids]][0][0]) 
            if _tv_price != 0 and abs(order_price - _tv_price) / _tv_price > slip_effi:
                print("slip")
                time.sleep(0.5)
                continue
            order_response = client.futures_create_order(
                symbol=_symbol, side=_side, type=_order_type, price=order_price, quantity=float(step_round.format(_quantity - executedQty)), newClientOrderId = orderID, timeInForce=_tif, reduceOnly = _reduceOnly)
            time.sleep(0.5)
            orderStatus = orderQuery(_symbol, orderID)
            executedQty += float(orderStatus['executedQty'])
            if executedQty >= _quantity:
                print(orderID)
                print(orderStatus['avgPrice'])
                print(filled)
                break
        if _force and filled == 20:
            order_response = client.futures_create_order(
                symbol=_symbol, side=_side, type=FUTURE_ORDER_TYPE_MARKET, quantity=float(step_round.format(_quantity - executedQty)), newClientOrderId=_OrderId+'_M')
        return order_response
    except Exception as e:
        print("an exception occured - {}".format(e))
        if '2022' in str(e):
            print('Nothing worried.')
            return True
        # print(str(e))
        # if "=-2021)" in str(e):
        #     return [False, "㊣"]
        return False


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
    client.futures_cancel_all_open_orders(symbol=symbol)
    total_position = float(client.futures_position_information(
        symbol=symbol)[0]["positionAmt"])
    if total_position == 0:
        print("\nCLOSE_ALL BUT NOTHING TO CLOSE\n")
        return True
    side = 0 if total_position < 0 else 1
    asksbids = 0 if side == 1 else 1
    total_position = abs(total_position)
    _orderId_tmp = f"errorClose_qty_{total_position}"
    close_params = {"_side": SIDE[side], "_quantity": float(step_round.format(total_position)), "_symbol": symbol, "_OrderId": _orderId_tmp,
                    "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif":"IOC", "_asksbids" : asksbids, "_force" : True, "_reduceOnly" : True}
    return order(**close_params)


@app.route('/')
def welcome():
    return render_template('index.html')

# max algo order num


@app.route('/test', methods=['POST'])
def test():
    return json.dumps(orderQuery("ETHUSDT","S_PREFIX_1"))
    # return client.futures_ticker(symbol="BTCUSDT")['lastPrice']  # last price
    # return client.futures_position_information(symbol="BTCUSDT")  # last price
    # try:
    #     client.futures_get_order(symbol = "ETHUSDT",origClientOrderId='dne')
    # except Exception as e:
    #     print('2013' in str(e))
    # # print('2013' in str(client.futures_get_order(symbol = "ETHUSDT",origClientOrderId='dne')))
    # # return json.dumps(client.futures_get_order(symbol = "ETHUSDT",origClientOrderId='dne'))
    # return(json.dumps(client.futures_order_book(symbol="BTCUSDT", limit=5)['asks'][0]))

    # data = json.loads(request.data)
    # size = data['strategy']['position_size']
    test_params = {"_side": "SELL", "_price" : 1532.14,"_quantity": 0.01, "_symbol": "ETHUSDT", "_OrderId": "S_PREFIX_1",
                   "_order_type": FUTURE_ORDER_TYPE_LIMIT}
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
    return json.dumps(close_all("ETHUSDT"))
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
@app.route('/webhook', methods=['POST'])  # 單有可能沒買到

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
    orderType = data['strategy']['alert_message']['orderType']
    if orderType == '0':
        print("\n\n NA \n\n")
        return {
            "code": "None",
            "message": "NA"
        }
    elif orderType == '5':
        print("\n\n CHANGE SIDE \n\n")
        return {
            "code": "None",
            "message": "change side"
        }
    OrderId = data['strategy']['alert_message']["origOrderId"].upper()
    
    symbol = data['ticker'].replace('PERP', '')
    ticksize = 1 if symbol == "BTCUSDT" else 2
    side = 0 if data['strategy']['order_action'].upper() == "BUY" else 1    # 0 == buy; 1 == sell
    asksbids = 0 if side == 1 else 1
    total_position = float(client.futures_position_information(
        symbol=symbol)[0]["positionAmt"])
    order_response = True
    if orderType == '2' or orderType == '3':    # TP1 / TP2
        executedQty = ordersQuery(symbol,  OrderId+'_1', _message = f'from TP{int(orderType) - 1}')
        order_params = {"_side": SIDE[side], "_quantity": float(step_round.format(executedQty / 2.0)), "_symbol": symbol, "_OrderId": OrderId + '_' + orderType,
                        "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif":"IOC", "_asksbids" : asksbids, "_force" : True, "_reduceOnly" : True}
        order_response = order(**order_params)
    # elif orderType == '3':  # TP2
    #     origOrder_1 = orderQuery(symbol, OrderId+'_1_1')
    #     origOrder_2 = orderQuery(symbol, OrderId+'_2_1')
    #     if not origOrder_1 or not origOrder_2:
    #         return {
    #         "code": "error",
    #         "message": "TP2 query failed"
    #     }
    #     order_params = {"_side": SIDE[side], "_quantity": float(origOrder_2["origQty"]), "_symbol": symbol, "_OrderId": OrderId + "_3",
    #                     "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif":"IOC", "_asksbids" : asksbids, "_force" : True, "_reduceOnly" : True}
    #     order_response = order(**order_params)
    elif orderType == '4':    # SL
        executedQty = ordersQuery(symbol, OrderId+'_1', _message = "from stopLoss")
        origOrder_2 = ordersQuery(symbol, OrderId+'_2', True, _message = "from stopLoss")
        if origOrder_2:
            executedQty = float(step_round.format(executedQty / 2.0))
        order_params = {"_side": SIDE[side], "_quantity": executedQty, "_symbol": symbol, "_OrderId": OrderId + "_4",
                        "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif":"IOC", "_asksbids" : asksbids, "_force" : True, "_reduceOnly" : True}
        order_response = order(**order_params)
    
    # ———————————————————————————[variables]————————————————————————————————————
    elif orderType == '1':   # place order's orderID : L_{timestamp}_1  /  S_{timestamp}_1
        if (total_position > 0 and side == 1) or (total_position < 0 and side == 0):
            print("\n\nCHANGE SIDE\n\n")
            orderid_tmp = "xLbyShort" if total_position > 0 else "xSbyLong"
            order_params_close_all = {"_side": SIDE[side], "_quantity": abs(total_position), "_symbol": symbol, "_OrderId": orderid_tmp,
                                    "_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif":"IOC", "_asksbids" : asksbids, "_force" : True, "_reduceOnly" : True}
            close_order = order(**order_params_close_all)
            print(close_order)
        print("\n\nPLACE_ORDER\n\n")
        risk = 0.01
        initial_capital = float(client.futures_account()[
                                'assets'][3]['walletBalance'])
        SL_diff = float(data['strategy']['alert_message']['SL_diff'])
        tv_price = float(str(data['strategy']['order_price'])[:6 + ticksize])
        halfQty = float(step_round.format((initial_capital / tv_price) / 2 if (initial_capital * risk / SL_diff * tv_price >
                                                                                initial_capital) else (initial_capital * risk / SL_diff) / 2))
        quantity = float(step_round.format(halfQty + halfQty))
        order_params_1 = {"_side": SIDE[side], "_quantity": quantity, "_symbol": symbol, "_OrderId": OrderId+'_1',   # First
                                "_tv_price" : tv_price,"_order_type": FUTURE_ORDER_TYPE_LIMIT, "_tif": "IOC", "_asksbids" : asksbids, "_force" : True}
        order_response = order(**order_params_1)        
        
    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")
        close_all(symbol)
        return {
            "code": "error",
            "message": "order failed",
        }
