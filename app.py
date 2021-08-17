import perspective
import tornado
import logging
from threading import Thread

import perspective
import tornado

from schemas import *
from deribit_client import *
from queue import Queue


def producer(q):
    exchange_info = DeribitClient.get_exchange_info("BTC")
    symbols = [el['instrument_name'] for el in exchange_info]
    symbols.remove("BTC-PERPETUAL")
    # print(symbols)
    # input()
    c = DeribitClient(symbols, q)
    c.start_stream()

def consumer(table, q: Queue):
    while True:
        try:
            res = q.get()
            table_update = DeribitClient.clean_response(res)
            table.update([table_update])
        except KeyError:
            continue

class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def get(self):
        self.render("index.html")

Table = perspective.Table(future_product_schema, index='sym')
MANAGER = perspective.PerspectiveManager()
MANAGER.host_table('data_source_one',Table)
app = tornado.web.Application(
    [
        # create a websocket endpoint that the client Javascript can access
        (
            r"/websocket",
            perspective.PerspectiveTornadoHandler,
            {"manager": MANAGER, "check_origin": True},
        ),
        (r"/", MainHandler),
    ]
)
app.listen(8888)
logging.critical("Listening on http://localhost:8888")
loop = tornado.ioloop.IOLoop.current()

q = Queue()

# Make separate thread for the producer
t1 = Thread(target=producer, args=(q,))
t1.daemon = True

# consumer should  not be run in separate thread so you can stop the program with ctrl+ c
# ctrl+ c only work on the main thread
t2 = Thread(target=consumer, args=(Table, q,))
t2.daemon = True

t1.start()
t2.start()


loop.start()
