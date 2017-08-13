import aiohttp
from lxml import html
from utils import UserAgent


class Getter:
    def __init__(self):
        self.urls = [
            'http://www.iphai.com/free/ng',
            'http://www.iphai.com/free/np'
        ]

    async def get_proxy(self, timeout=60):
        headers = {
            'User-Agent': UserAgent.random()
        }
        proxies = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for url in self.urls:
                async with session.get(url, timeout=timeout) as r:
                    content = await r.text()
                selector = html.fromstring(content)
                ul_list = selector.xpath('.//table//tr')
                for ul in ul_list[1:]:
                    ips = ul.xpath('./td/text()')[0:2]
                    proxy = ':'.join(map(lambda x: x.strip(' \t\n'), ips))
                    proxies.append(proxy)
        return proxies
