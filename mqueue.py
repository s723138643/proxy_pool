import heapq

from asyncio import Event
from asyncio import Queue, QueueEmpty
from asyncio.coroutines import coroutine


class MQueue(Queue):
    """Notice: the item which get() method return is unordered"""
    def __init__(self, maxsize=0, *, loop=None):
        super().__init__(maxsize=maxsize, loop=loop)
        self.empty_event = Event(loop=self._loop)
        self.empty_event.set()

    def _init(self, maxsize):
        # make item unique
        self._queue = set()

    def _get(self):
        # Warn: shouldn't call this method derictly
        return self._queue.pop()

    def _put(self, item):
        # Warn: shouldn't call this method derictly
        self._queue.add(item)

    def __contains__(self, item):
        return item in self._queue

    def get_nowait(self):
        item = super().get_nowait()
        if self.empty():
            self.empty_event.set()
        return item

    @coroutine
    def get(self, maxcount=1):
        """pop almost maxcount items from queue,
        blocking when queue is empty
        """
        while self.empty():
            getter = self._loop.create_future()
            self._getters.append(getter)
            try:
                yield from getter
            except:
                getter.cancel()  # Just in case getter is not done yet.
                if not self.empty() and not getter.cancelled():
                    # We were woken up by put_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._getters)
                raise
        items = []
        while not self.empty() and maxcount > 0:
            items.append(self._get())
            maxcount -= 1
        if self.empty():
            # notify others queue is empty
            self.empty_event.set()
        return items

    @coroutine
    def get_all(self):
        """get all items form queue but not remove,
        blocking when queue is empty
        """
        while self.empty():
            getter = self._loop.create_future()
            self._getters.append(getter)
            try:
                yield from getter
            except:
                getter.cancel()
                if not self.empty() and not getter.cancelled():
                    self._wakeup_next(self._getters)
                raise
        return list(self._queue)

    def put_nowait(self, item):
        if item in self._queue:
            return
        super().put_nowait(item)
        self.empty_event.clear()


class HQueue(MQueue):
    def _init(self, maxsize):
        self._queue = set()
        self._deadline = list()

    def _get(self):
        while self._deadline and self._queue:
            deadline, item = heapq.heappop(self._deadline)
            if item not in self._queue:
                continue
            self._queue.remove(item)
            return item

    def _put(self, item):
        assert isinstance(item, tuple), ValueError('Excepted a tuple object')
        self._queue.add(item[1])
        heapq.heappush(self._deadline, item)

    def get_dead(self, count=0):
        timeouts = []
        while self._deadline:
            deadline = self._deadline[0][0]
            if self._loop.time() > deadline:
                timeouts.append(self.get_nowait())
            else:
                break
        return timeouts


async def test():
    queue = MQueue()
    for i in range(100):
        await queue.put(i % 50)

    if 3 not in queue:
        print('get contains failed')
    print(await queue.get_all())
    print(await queue.get(11))
    print(await queue.get_all())
    print(await queue.get(queue.qsize()))
    if queue.empty() and not queue.empty_event.is_set():
        print('test failed, queue is empty but event is not set')
    print(queue.qsize())
    queue.put_nowait(4)
    print(await queue.get_all())


if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
