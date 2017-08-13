import re
import aiohttp
from utils import UserAgent


class Getter:
    def __init__(self, count=100):
        self.url = ("http://www.66ip.cn/mo.php?sxb=&tqsl={}&port=&export="
                    "&ktip=&sxa=&submit=%CC%E1++%C8%A1&textarea=")
        self.count = count

    async def get_proxy(self, timeout=60):
        headers = {
            'User-Agent': UserAgent.random()
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            url = self.url.format(self.count)
            async with session.get(url, timeout=timeout) as r:
                content = await r.text()
        return re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}',
                          content)
