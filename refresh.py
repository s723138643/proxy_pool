import logging
import asyncio
import aiohttp
import pathlib
import importlib
import settings


plugin_path = 'proxy_getter'
plugin_class = 'Getter'
logger = logging.getLogger('Refresh')


def find_getter(path, class_name):
    p = pathlib.Path(path)
    if not p.is_dir():
        raise TypeError('find_getter must work with directory')
    getters = []
    for f in p.iterdir():
        if f.suffix != '.py':
            continue
        module_str = str(f.with_suffix('')).replace('/', '.')
        try:
            module = importlib.import_module(module_str)
            getters.append((module_str, getattr(module, class_name)))
        except (ImportError, AttributeError) as e:
            logger.error('import module:{} failed'.format(module_str))
            logger.exception(e)
    return getters


class Proxy:
    def __init__(self, verify, usable, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._verify = verify
        self._usable = usable

    async def get(self, plugin, timeout=60):
        module, GetterClass = plugin
        try:
            getter = GetterClass()
            proxies = await getter.get_proxy(timeout=timeout)
        except asyncio.TimeoutError:
            logger.warn('get proxies from {} timeout'.format(module))
            return
        except aiohttp.ClientError:
            logger.warn('get proxies from {} failed'.format(module))
            return
        logger.info('from {} got {} proxies'.format(module, len(proxies)))
        for proxy in set(proxies):
            if not proxy or proxy in self._usable:
                continue
            await self._verify.put(proxy)

    async def get_proxy(self, concurrences=5, timeout=60):
        getters = find_getter(plugin_path, plugin_class)
        start = 0
        while start < len(getters):
            plugins = getters[start:start+concurrences]
            tasks = [self.get(plugin, timeout) for plugin in plugins]
            await asyncio.wait(tasks, timeout=timeout)
            start += concurrences

    async def serve_forever(self, threads=5):
        uevent = self._usable.empty_event
        vevent = self._verify.empty_event
        fetch_timeout = settings.FETCH_TIMEOUT
        fetch_interval = settings.FETCH_INTERVAL
        interval = settings.REFRESH_INTERVAL
        while True:
            try:
                await self.get_proxy(threads, fetch_timeout)
            except Exception as e:
                logger.error('uncatched error')
                logger.exception(e)

            try:
                start = self._loop.time()
                await asyncio.wait_for(vevent.wait(), timeout=interval)
                remain = interval + start - self._loop.time()
                if remain <= 0:
                    continue
                await asyncio.wait_for(uevent.wait(), timeout=remain)
                spent = self._loop.time() - start
                if spent < fetch_interval:
                    await asyncio.sleep(fetch_interval - spent)
            except asyncio.TimeoutError:
                '''it seem that we spent REFRESH_INTERVAL seconds'''
                pass
            
            for proxy in self._usable.get_dead():
                await self._verify.put(proxy)


if __name__ == '__main__':
    find_getter('proxy_getter')
