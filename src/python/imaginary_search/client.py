import asyncio
import hashlib
import json
import logging
import pathlib
import time

from typing import Optional

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


class ServiceClient:
    """
    Client with synchronized token class.
    Idea from here: https://stackoverflow.com/a/27401341/5672940
    """
    _internal_lock = asyncio.Lock()
    _renew_marker = True
    _token = None

    def __init__(self, base_url: str, api_key: str, image_folder: str = '.',
            resource: str = 'images', index_fields = None, chunk_size: int = 1024,
            cache_timeout: int = 3600, concurrency: int = 10) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.auth_url = f'{self.base_url}/auth'
        self.resource_url = f'{self.base_url}/{resource}'
        self.image_folder = pathlib.Path(image_folder)
        self.image_folder.mkdir(parents=True, exist_ok=True)
        self.cache_timeout = cache_timeout
        self.chunk_size = chunk_size
        self.pages = {}
        self.items = {}
        self.cache_task = None
        self.index = {}

    async def render_auth_headers(self) -> dict:
        return {'Authorization': await self.get_auth_token()}

    async def _renew(self) -> None:
        async with aiohttp.ClientSession() as session:
            req_kwargs = dict(url=self.auth_url, json={'apiKey': self.api_key})
            print(f'req_kwargs: {req_kwargs}')
            async with session.post(**req_kwargs) as response:
                data = await response.json()
                if data['auth']:
                    print(f'Response: {data}')
                    self._token = data['token']
                else:
                    print(f'auth is False')

    async def get_auth_token(self) -> str:
        async with self._internal_lock:
            if self._renew_marker:
                await self._renew()
                self._renew_marker = False
            return self._token

    # Marks the token to be refreshed at the next get()
    async def set_renew_token(self) -> None:
        async with self._internal_lock:
            self._renew_marker = True

    async def fetch_url(self, session, url, params=None) -> dict:
        data = None
        retries = 0
        while data is None:
            params = params or dict()
            headers = await self.render_auth_headers()
            req_kwargs = dict(url=url, params=params, headers=headers)
            try:
                async with session.get(**req_kwargs) as response:
                    response.raise_for_status()
                    data = await response.json()
                    print(f'Response data: {data}')
            except aiohttp.ClientError as e:
                print(e)
                retries += 1
                if MAX_RETRIES <= retries:
                    print('Max retries reached')
                    break
            # except the expired token error and renew it
            # self.set_renew_token()
        return data

    async def get_page(self, session, page_num: int = 1):
        print(f'Fetching page_num={page_num}')
        return await self.fetch_url(session, self.resource_url, {'page': page_num})

    async def get_item_info(self, session, item_id: int):
        print(f'Fetching item_id={item_id}')
        return await self.fetch_url(session, f'{self.resource_url}/{item_id}')

    @staticmethod
    def calculate_checksum(obj: dict):
        return hashlib.md5(json.dumps(obj).encode('utf-8')).hexdigest()

    async def save_image(self, session, url: str) -> str:
        file_path = self.image_folder / url.split('/')[-1]
        print(f'Saving url={url} -> file_path={file_path}')
        async with session.get(url) as response:
            async with aiofiles.open(file_path, mode='wb') as stream:
                while True:
                    chunk = await response.content.read(self.chunk_size)
                    if not chunk:
                        break
                    await stream.write(chunk)
        print(f'Saved url={url} -> file_path={file_path}')
        return file_path

    async def process_page(self, session, page):
        # validate page here
        print(f'page: {page}')
        required_fields = ['pictures', 'page', 'hasMore', 'pageCount']
        if any(map(lambda x: x not in page.keys(), required_fields)):
            error_text = 'Invalid page data'
            print(f'{error_text}: {page}')
            raise ValueError(error_text)

        page_key = self.calculate_checksum(page)
        if page_key not in self.pages:
            self.pages[page_key] = page

        await asyncio.gather(*(self.save_item(session, item['id'])
                               for item in page['pictures']))

    def save_to_index(self, item_data):
        print
        for value in item_data.values():
            curr_values = self.index.get(value.lower(), [])
            self.index[value.lower()] = curr_values + [item_data['id']]

    async def save_item(self, session, item_id):
        item_data = await self.get_item_info(session, item_id)
        print(f'ITEM DATA: {item_data}')
        self.items[item_id] = item_data
        self.save_to_index(item_data)
        return await asyncio.gather(
            *(self.save_image(session, item_data['cropped_picture']),
              self.save_image(session, item_data['full_picture'])))

    def start_cache_check(self):
        async def wrapper():
            while True:
                print('starting load_cache task')
                await self.load_cache()
                print(f'waiting for cache timeout to run out: {self.cache_timeout}')
                await asyncio.sleep(self.cache_timeout)

        self.cache_task = asyncio.ensure_future(wrapper())

    async def load_cache(self):
        print(f'load_cache start')
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            has_more = True
            page_num = 1
            while has_more:
                page = await self.get_page(session, page_num)
                # validate page somehow
                if page is None:
                    raise ValueError('Could not fetch page from API')

                try:
                    await self.process_page(session, page)
                except Exception as e:
                    print(e)
                    break

                is_last_page = page['pageCount'] == page_num
                # is_last_page = not page['hasMore']
                has_more = page['hasMore']
                page_num += 1
        print(f'load_cache end')

    def find_images_by_term(self, term: str):
        results = []
        for idx_key in self.index.keys():
            if term in idx_key:
                results += [self.items[item_id]
                            for item_id in self.index[idx_key]]
        return results
