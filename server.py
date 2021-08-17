from queue import Queue
from deribit_client import DeribitClient
from threading import Thread
import json
import sys


def clean_response(response: str):
    temp = json.loads(response)

    return temp['params']['data']


def producer(q):
    exchange_info = DeribitClient.get_exchange_info("BTC")
    symbols = [el['instrument_name'] for el in exchange_info]
    symbols.remove("BTC-PERPETUAL")
    # print(symbols)
    # input()
    c = DeribitClient(symbols, q)
    c.start_stream()


def consumer(q: Queue):
    while True:
        try:
            res = q.get()
            print(DeribitClient.clean_response(res))
        except KeyError:
            continue


q = Queue()

# Make separate thread for the producer
t1 = Thread(target=producer, args=(q,))
t1.daemon = True
t1.start()

# consumer should  not be run in separate thread so you can stop the program with ctrl+ c
# ctrl+ c only work on the main thread
consumer(q)
