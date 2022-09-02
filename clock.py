from apscheduler.schedulers.blocking import BlockingScheduler
import urllib.request
from binance.client import Client
import config

sched = BlockingScheduler()
client = Client(config.API_KEY, config.API_SECRET, testnet=True)


@sched.scheduled_job('cron', day_of_week='mon-fri', minute='*/1')
def scheduled_job():
    client.futures_change_leverage(symbol="BTCUSDT", leverage=10)
    client.futures_change_leverage(symbol="ETHUSDT", leverage=10)
    url = "https://tv-binance-bot.herokuapp.com/"
    conn = urllib.request.urlopen(url)

    for key, value in conn.getheaders():
        print(key, value)


sched.start()
