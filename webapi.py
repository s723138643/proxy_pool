import json

from aiohttp import web


async def usage(request):
    result = {
        'get': 'get one proxy and remove it from queue',
        'get_all': 'get all proxies and do not remove them from queue',
        'get_total': 'get total count of proxies'
    }
    text = json.dumps(result)
    return web.Response(body=text, content_type='application/json')


async def get_one(request):
    usable = request.app['usable_queue']
    proxy = await usable.get(1)
    result = json.dumps({'result': proxy[0]})
    return web.Response(body=result, content_type='application/json')


async def get_all(request):
    usable = request.app['usable_queue']
    proxies = await usable.get_all()
    result = json.dumps({'result': proxies})
    return web.Response(body=result, content_type='application/json')


async def get_total(request):
    usable = request.app['usable_queue']
    result = json.dumps({'result': usable.qsize()})
    return web.Response(body=result, content_type='application/json')


def set_routes(app):
    app.router.add_get('/', usage)
    app.router.add_get('/get', get_one)
    app.router.add_get('/get_all', get_all)
    app.router.add_get('/get_total', get_total)

    return app


if __name__ == '__main__':
    from mqueue import MQueue

    queue = MQueue()
    queue.put_nowait('a')
    queue.put_nowait('b')

    app = web.Application()
    app['usable_queue'] = queue
    set_routes(app)

    web.run_app(app)
