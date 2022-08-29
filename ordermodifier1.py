import time
from binance.streams import ThreadedWebsocketManager
import config


def handler(order_data):
    print(order_data)


manager = ThreadedWebsocketManager(
    config.API_KEY,
    config.API_SECRET,
    testnet=True
)

manager.daemon = True  # ctrl-c works
manager.start()
manager.start_futures_user_socket(handler)

while True:
    # run your other code here
    time.sleep(0.1)
