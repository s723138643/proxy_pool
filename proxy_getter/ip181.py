import aiohttp
from lxml import html
from utils import UserAgent


class Getter:
    def __init__(self, count=100):
        self.url = 'http://www.ip181.com/'

    async def get_proxy(self, timeout=60):
        headers = {
            'User-Agent': UserAgent.random()
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(self.url, timeout=timeout) as r:
                content = await r.text()
        proxies = []
        selector = html.fromstring(content)
        tr_list = selector.xpath('//tr')[1:]
        for tr in tr_list:
            ips = tr.xpath('./td/text()')[0:2]
            proxy = ':'.join(map(lambda x: x.strip(' \t\n'), ips))
            proxies.append(proxy)
        return proxies
