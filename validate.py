import logging
import asyncio
import aiohttp
import settings

from collections import deque
from utils import UserAgent


logger = logging.getLogger('Validate')


def random_headers():
    headers = {
        'User-Agent': UserAgent.random()
    }
    return headers


def check_ip(ip: str):
    result = ip.split('.')
    if len(result) != 4:
        return False
    for digit in result:
        if not digit or len(digit) > 3 or digit.startswith('0'):
            return False
        try:
            num = int(digit)
        except:
            return False
        if num >= 255 or num == 0:
            return False
    return True


def check_port(port: str):
    try:
        p = int(port)
    except:
        return False
    if 0 < p < 65536:
        return True
    else:
        return False


def check_host(host: str):
    # only support ipv4
    result = host.split(':')
    lens = len(result)
    if lens == 1:
        return check_ip(result[0])
    elif lens == 2:
        ip, port = result
        return check_ip(ip) and check_port(port)
    else:
        return False


class SessionPool:
    def __init__(self, maxsize=20, *, loop=None):
        self._closed = False
        if not isinstance(maxsize, int) or maxsize <= 0:
            raise ValueError('"maxsize" must be a positive integer')
        self._maxsize = maxsize
        self._size = 0
        self._loop = loop or asyncio.get_event_loop()
        self._ready = set()
        self._sched = set()
        self._waiters = deque()

    async def get(self):
        if not self._ready and self._size < self._maxsize:
            session = aiohttp.ClientSession(loop=self._loop)
            self._size += 1
            self._sched.add(session)
            return session

        while not self._ready:
            fut = self._loop.create_future()
            self._waiters.append(fut)
            try:
                await fut
            except:
                fut.cancel()
                if self._ready and not fut.cancelled():
                    self._wakeup_next(self._waiters)
                raise
        session = self._ready.pop()
        self._sched.add(session)
        return session

    def _wakeup_next(self, waiters):
        while waiters:
            fut = waiters.popleft()
            if fut.done() or fut.cancelled():
                continue
            fut.set_result(None)
            return

    def _put(self, session):
        self._ready.add(session)
        self._wakeup_next(self._waiters)

    def release(self, session):
        self._put(session)
        self._sched.remove(session)

    def close(self):
        self._closed = True
        assert len(self._ready)+len(self._sched) == self._size
        for session in self._ready:
            session.close()
        for session in self._sched:
            session.close()

    def __del__(self):
        if not self._closed:
            self.close()


class Consumer:
    def __init__(self, verify, usable, threads=15, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._pool = SessionPool(maxsize=threads, loop=self._loop)
        self._verify_queue = verify
        self._usable_queue = usable
        self._threads = threads

    async def test(self, target, proxy, timeout):
        if not check_host(proxy):
            return False, proxy
        http_proxy = 'http://' + proxy
        try:
            session = await self._pool.get()
            response = await session.get(
                target, headers=random_headers(),
                proxy=http_proxy, timeout=timeout
                )
        except Exception as e:
            # ignore all exception
            return False, proxy
        finally:
            self._pool.release(session)
        if response.status != 200:
            #print('{} is unusable'.format(proxy))
            return False, proxy
        return True, proxy

    async def verify(self, proxy):
        usable, _proxy = await self.test(
            settings.VERIFY_TARGET, proxy, settings.VERIFY_TIMEOUT
        )
        if usable:
            logger.info('{} is usable'.format(proxy))
            deadline = self._loop.time() + settings.REFRESH_INTERVAL
            await self._usable_queue.put((deadline, proxy))

    async def serve_forever(self):
        while True:
            proxy = await self._verify_queue.get()
            self._loop.create_task(self.verify(proxy[0]))


async def test_pool(loop):
    pool = SessionPool(1, loop=loop)
    s = await pool.get()
    print('got session: {}'.format(s))
    print('get release session: {}'.format(s))
    pool.release(s)
    a = await pool.get()
    print('got session: {}'.format(a))
    pool.close()


async def test_consumer(loop):
    proxy = [
        '449..68.2552.88:8750',
        '115.52.197.19:9999',
        '114.102.35.48:8118',
        '118.80.201.125:8118',
        '181833.222..101022..101000:8179',
        '5588.243.3.227.20:8548',
        '180.173.3.109.14499:8866'
    ]
    cur = Consumer(None, None)
    coros = []
    for p in proxy:
        coro = cur.test(settings.VERIFY_TARGET, p, 30)
        coros.append(coro)
    done, pending = await asyncio.wait(coros)
    for f in done:
        usable, proxy = f.result()
        if usable is True:
            print('{} is usable'.format(proxy))
        else:
            print('{} is unusable'.format(proxy))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_pool(loop))
    loop.run_until_complete(test_consumer(loop))
