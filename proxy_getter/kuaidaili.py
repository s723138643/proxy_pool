import asyncio
import aiohttp
from lxml import html
from utils import UserAgent

class Getter:
    def __init__(self):
        self.urls = [
            'http://www.kuaidaili.com/free/inha/{}/',
            'http://www.kuaidaili.com/free/intr/{}/'
        ]
        self.total = 5

    async def get_proxy(self, timeout=60):
        proxies = []
        with aiohttp.ClientSession() as session:
            for url in self.urls:
                for i in range(1, self.total+1):
                    headers = {
                        'User-Agent': UserAgent.random()
                    }
                    target = url.format(i)
                    async with session.get(target, headers=headers, timeout=timeout) as r:
                        content = await r.text()
                    selector = html.fromstring(content)
                    tr_list = selector.xpath('//tbody/tr')
                    for tr in tr_list:
                        ip = tr.xpath('.//td[@data-title="IP"]/text()')
                        port = tr.xpath('.//td[@data-title="PORT"]/text()')
                        proxies.append(':'.join([ip[0], port[0]]))
                    await asyncio.sleep(3)
        return proxies


if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    getter = Getter()
    proxies = loop.run_until_complete(getter.get_proxy())
    print(proxies)