from apscheduler.schedulers.blocking import BlockingScheduler
import urllib
import urllib.request
from binance.client import Client
import config

sched = BlockingScheduler()
client = Client(config.API_KEY, config.API_SECRET, testnet=True)


@sched.scheduled_job('cron', day_of_week='mon-fri', minute='*/25')
def scheduled_job():
    client.futures_change_leverage(symbol="BTCUSDT", leverage=10)
    client.futures_change_leverage(symbol="ETHUSDT", leverage=10)
    client.futures_change_margin_type(symbol="BTCUSDT", marginType="ISOLATED")
    client.futures_change_margin_type(symbol="ETHUSDT", marginType="ISOLATED")
    url = "https://tv-binance-bot.herokuapp.com/"
    conn = urllib.request.urlopen(url)

    for key, value in conn.getheaders():
        print(key, value)


sched.start()
