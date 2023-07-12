import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import sched
import time
from binance.client import Client
from binance.enums import *
from talib import MA_Type
from binance.exceptions import BinanceAPIException
import talib
import threading
import numpy as np


#基本功能測
client = Client(api_key='YOUR_API_KEY', api_secret='YOUR_API_SECRET')
# 交易参数
symbol = "BTCBUSD"
interval = KLINE_INTERVAL_1MINUTE
# 技术指标参数
dma_short_period = 10
dma_long_period = 50
bband_period = 20 
bband_deviation = 2
rsi_period = 14

#line設定
# Line Notify API token
access_token = 'EIdkNhlveGtRVUl2r85WRBqSGCo4lzGmtLUjm3EKYLw'

# Line Notify API endpoint
url = 'https://notify-api.line.me/api/notify'

# Line Notify message parameters
headers = {'Authorization': f'Bearer {access_token}'}

def run_notify_program():
    # 設定目標時間為每天的 7:00 AM
    tz = pytz.timezone('Asia/Taipei')
    target_time = datetime.now(tz).replace(hour=7, minute=0, second=0, microsecond=0)

    def run_program(scheduler):
        # 開始執行程式
        
        url = "https://news.cnyes.com/news/cat/bc"

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 获取前 10 筆新闻标题
        news_list = soup.find_all("div", {"style": "height:70px;"})[:10]

        for news in news_list:
            # 找到新闻标题和日期
            title = news.find("a").text.strip()
            link = news.find("a")["href"]
            # 將文字部分轉換為繁體中文
            title = title.encode('big5', 'ignore').decode('big5')
            print(title)
            print("https://news.cnyes.com"+link)
            # 設定 Line Notify API 的请求头和请求体
            headers = {
                "Authorization": "Bearer " + 'EIdkNhlveGtRVUl2r85WRBqSGCo4lzGmtLUjm3EKYLw', 
                "Content-Type": "application/x-www-form-urlencoded"
            }
            message = "\n".join([title, "https://news.cnyes.com"+link, "----------------------"])
            payload = {"message": message}

            # 发送 POST 请求
            r = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload)

        radar_url = 'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0058-003?Authorization=rdec-key-123-45678-011121314&format=JSON'
        radar = requests.get(radar_url)
        radar_json = radar.json()
        radar_img = radar_json['cwbopendata']['dataset']['resource']['uri']
        radat_time = radar_json['cwbopendata']['dataset']['time']['obsTime']   # 取得時間
        print(radar_img)
        url = 'https://notify-api.line.me/api/notify'    # LINE Notify API 網址
        token = '你的 LINE Notify 權杖'                   # 自己申請的 LINE Notify 權杖
        headers = {
            'Authorization': 'Bearer ' + 'EIdkNhlveGtRVUl2r85WRBqSGCo4lzGmtLUjm3EKYLw'   
        }
        data = {
            'message':'從雷達回波看看會不會下雨～',   # 發送的訊息
            'imageThumbnail':radar_img,          # 預覽圖網址
            'imageFullsize':radar_img            # 完整圖片網址
        }
        data = requests.post(url, headers=headers, data=data)    # 發送 LINE NOtify
        print("Finished running program.")

        # 計算下一次執行的時間
        next_day = datetime.now(tz) + timedelta(days=1)
        target_time = next_day.replace(hour=7, minute=0, second=0, microsecond=0)

        # 使用 sched 模块設定下一次執行的時間
        scheduler.enterabs(target_time.timestamp(), 1, run_program, (scheduler,))

    # 使用 sched 模块設定第一次執行的時間
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enterabs(target_time.timestamp(), 1, run_program, (scheduler,))
    scheduler.run()
def singel():
    while True:
        try:
            # 获取历史 K 线数据
            klines = client.futures_klines(symbol=symbol, interval=interval, limit=200)
            close_prices = np.array([float(kline[4]) for kline in klines])

            # 计算 DMA 指标
            dma_short = talib.SMA(close_prices, timeperiod=dma_short_period)
            dma_long = talib.SMA(close_prices, timeperiod=dma_long_period)

            # 计算 BB 指标
            upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=bband_period, nbdevup=bband_deviation, nbdevdn=bband_deviation, matype=MA_Type.SMA)

            # 计算 RSI 指标
            rsi = talib.RSI(close_prices, timeperiod=rsi_period)

            # 获取最新的价格信息
            ticker = client.get_symbol_ticker(symbol=symbol)

            # 提取当前的价格
            price = float(ticker['price'])

            # 判断买入和卖出信号
            if dma_short[-1] > dma_long[-1] and price < lower_band[-1] and rsi[-1] < 30:
                message = '買入信號，建議做多（短線策略）''{} 價格: ${:.2f}'.format(symbol, price)
                response = requests.post(url, headers=headers, data={'message': message})
                if response.status_code != 200:
                    print('发送Line通知出错：', response.text)
                
            elif dma_short[-1] < dma_long[-1] and price > upper_band[-1] and rsi[-1] > 70:
                message = '賣出信號，建議做空（短線策略）''{} 價格: ${:.2f}'.format(symbol, price)
                response = requests.post(url, headers=headers, data={'message': message})
                if response.status_code != 200:
                    print('发送Line通知出错：', response.text)
               
            # 输出判断状态
            else:
                # 输出当前价格
                print('{} 價格: ${:.2f}'.format(symbol, price))
                
                
            # 等待 1 分钟后再次获取价格
            time.sleep(60)

        

        except BinanceAPIException as e:
            print(e)
            
            
b = threading.Thread(target=singel)  
a = threading.Thread(target=run_notify_program)

a.start()  # 啟用執行緒
b.start()  # 啟用執行緒
