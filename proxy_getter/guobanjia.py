import aiohttp
from lxml import html
from utils import UserAgent


class Getter:
    def __init__(self, count=100):
        self.url = "http://www.goubanjia.com/free/gngn/index{page}.shtml"

    async def get_proxy(self, timeout=60):
        headers = {
            'User-Agent': UserAgent.random()
        }
        proxies = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for page in range(1, 10):
                url = self.url.format(page=page)
                async with session.get(url, timeout=timeout) as r:
                    content = await r.text()
                selector = html.fromstring(content)
                proxy_list = selector.xpath('//td[@class="ip"]')
                for each_proxy in proxy_list:
                    ips = each_proxy.xpath('.//text()')
                    proxy = ''.join(map(lambda x: x.strip(' \t\n'), ips))
                    proxies.append(proxy)
        return proxies

