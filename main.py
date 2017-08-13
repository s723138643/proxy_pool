import logging
import asyncio
import aiohttp
import settings

from refresh import Proxy
from validate import Consumer
from mqueue import MQueue, HQueue
from webapi import set_routes


config = {
    'format': settings.LOGFMT,
    'datefmt': settings.LOGDATEFMT,
    'level': settings.LOGLEVEL
}
logging.basicConfig(**config)

def main():
    usable_queue = HQueue()
    verify_queue = MQueue()
    loop = asyncio.get_event_loop()

    proxy = Proxy(verify=verify_queue, usable=usable_queue, loop=loop)
    consumer = Consumer(verify=verify_queue, usable=usable_queue, loop=loop)

    app = aiohttp.web.Application(loop=loop)
    app['usable_queue'] = usable_queue
    set_routes(app)

    try:
        fetcher = loop.create_task(proxy.serve_forever())
        verify = loop.create_task(consumer.serve_forever())
        aiohttp.web.run_app(
            app,
            host=settings.SERVER_HOST, port=settings.SERVER_PORT,
            loop=loop
            )
    finally:
        loop.run_until_complete(app.shutdown())
        if not (verify.done() or verify.cancelled()):
            verify.cancel()
        if not (fetcher.done() or fetcher.cancelled()):
            fetcher.cancel()

if __name__ == '__main__':
    main()
