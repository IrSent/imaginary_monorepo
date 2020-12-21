import asyncio
import logging
# import pathlib
import os

from io import StringIO
from threading import Event, RLock
from threading import Lock

import aiofiles

from aiohttp import web

from .client import ServiceClient

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 3600
IMAGE_FOLDER = os.environ.get('IMAGE_FOLDER', './images/')
MAX_RETRIES = os.environ.get('MAX_RETRIES', 5)
BASE_URL = os.environ.get('BASE_URL', 'http://interview.agileengine.com')
API_KEY = os.environ.get('API_KEY', 'INCORRECT_API_KEY')
AUTH_URL = f'{BASE_URL}/auth'
routes = web.RouteTableDef()


@routes.get(r'/search/{search_term:\w+}')
async def search_handler(request):
    search_term = str(request.match_info['search_term']).lower()
    print(f'search_term: {search_term}')
    client = request.app['client']
    images = client.find_images_by_term(search_term)
    return web.json_response({'data': images})


async def _main():
    print(f'main start')
    app = web.Application()
    client = ServiceClient(
        base_url=BASE_URL, api_key=API_KEY, image_folder=IMAGE_FOLDER,
        cache_timeout=CACHE_TIMEOUT)
    client.start_cache_check()
    app['client'] = client
    app.add_routes(routes)
    return app


def main():
    web.run_app(_main())


if __name__ == 'main':
    web.run_app(_main())
