import websockets
import asyncio
import json
from queue import Queue
import requests

class DeribitClient:
    def __init__(self, instrument_names,producer_queue:Queue):
        self.instrument_names = instrument_names
        self.producer_queue = producer_queue
        pass
    
    @staticmethod
    def get_exchange_info(asset:str):
        assert asset == "BTC" or asset == "ETH", "asset must equal BTC or ETH"
        url = f"https://www.deribit.com/api/v2/public/get_instruments?currency={asset}&expired=false&kind=future"
        response = requests.get(url)
        response_dict = response.json()
        return response_dict['result']

    @staticmethod
    def clean_response(response: str):
        res = {}
        temp = json.loads(response)
        res['ts'] = temp['params']['data']['timestamp']
        res['sym'] = temp['params']['data']['instrument_name']
        res["BidP"] = temp['params']['data']["best_bid_price"]
        res["BidQ"] = temp['params']['data']["best_bid_amount"]
        res["AskP"] = temp['params']['data']["best_ask_price"]
        res["AskQ"] = temp['params']['data']["best_ask_amount"]

        return res

    async def handle_messages(self,msg):
        async with websockets.connect('wss://www.deribit.com/ws/api/v2') as websocket:
            await websocket.send(msg)
            while websocket.open:
                response = await websocket.recv()
                # do something with the notifications...
                self.producer_queue.put_nowait(response)

    def start_stream(self):
        msg = \
            {"jsonrpc": "2.0",
             "method": "public/subscribe",
             "id": 42,
             "params": {
                 "channels": [f"quote.{instrument_name}"for instrument_name in self.instrument_names]}
            }
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.handle_messages(json.dumps(msg)))
        # loop.call_later(60, task.cancel)
        loop.run_until_complete(task)
    
    # BTC-PERPETUAL
    

