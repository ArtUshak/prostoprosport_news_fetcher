from typing import Awaitable, Callable

import aiohttp
import pytest
import pytest_aiohttp
import pytest_asyncio
import tortoise.contrib.test

import models
import rss
from db import init_db
from news_fetcher import fetch_news_async


class MockApp:
    base_url: str = 'http://localhost'

    async def get_mock_rss(
        self, request: aiohttp.web.Request
    ) -> aiohttp.web.Response:
        return aiohttp.web.Response(
            body=f'''
            <?xml version="1.0" encoding="UTF-8"?>
            <!-- This is test RSS feed based on http://ria.ru/export/rss2/archive/index.xml -->
            <rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:rambler="http://news.rambler.ru" xmlns:mailru="http://news.mail.ru/" version="2.0">
            <channel>
                <title>Тест-новости</title>
                <link>{self.base_url}</link>
                <description>Тестовые новости в Руритании и мире, самая оперативная информация: темы дня, обзоры, анализ. Фото и видео с места событий, инфографика, радиоэфир, подкасты.</description>
                <language>ru</language>
                <copyright>TEST Novosti</copyright>
                <item>
                <title>Любовь на миллион</title>
                <link>{self.base_url}/news/million-bucks</link>
                <guid>{self.base_url}/news/million-bucks</guid>
                <testrian:priority xmlns:testrian="http://testrian.example.com/ns">3</testrian:priority>
                <pubDate>Sun, 03 Jul 2022 09:11:11 +0300</pubDate>
                <description>Сообщается, что любовница президента Руритании пожертвовала на благотворительность один миллион руританских долларов. Семья президента опровергла эту информацию.</description>
                <testrian:type xmlns:testrian="http://testrian.example.com/ns">article</testrian:type>
                <category>Лента новостей</category>
                </item>
                <item>
                <title>Чемоданный переполох</title>
                <link>{self.base_url}/news/railroad-station-suitcases</link>
                <guid>{self.base_url}/news/railroad-station-suitcases</guid>
                <testrian:priority xmlns:testrian="http://testrian.example.com/ns">3</testrian:priority>
                <pubDate>Sun, 03 Jul 2022 09:08:19 +0300</pubDate>
                <description>Бандиты из синдиката ЧЕМО украли 50 чемоданов с Северного Руританского вокзала. Возбуждено уголовное дело.</description>
                <testrian:type xmlns:testrian="http://testrian.example.com/ns">article</testrian:type>
                <category>Лента новостей</category>
                <enclosure url="http://cdn.img.example.com/images/chemodan0000.jpg.webp" type="image/jpeg"/>
                </item>
            </channel>
            </rss>
            '''
        )

    def get_aiohttp_app(self) -> aiohttp.web.Application:
        async def get_mock_rss(
            request: aiohttp.web.Request
        ) -> aiohttp.web.Response:
            return await self.get_mock_rss(request)

        app = aiohttp.web.Application()
        app.router.add_route(
            'GET', '/rss/rss.xml', get_mock_rss
        )
        # for page_url, page_content in pages.items():
        #     app.router.add_route(
        #         'GET', page_url, return_static_route(page_content)
        #     )
        return app


@pytest_asyncio.fixture(autouse=True)
async def fixture_db():
    await init_db('sqlite://:memory:')
    yield
    await tortoise.Tortoise._drop_databases()


@pytest.mark.asyncio
async def test_rss_fetch_news(
    aiohttp_server: Callable[
        [aiohttp.web.Application], Awaitable[pytest_aiohttp.plugin.TestServer]
    ]
) -> None:
    app = MockApp()

    server = await aiohttp_server(app.get_aiohttp_app())

    app.base_url = f'http://{server.host}:{server.port}'

    with open('data/test/rss.json', mode='rt') as config_file:
        module = rss.RSSModule(
            config_file, app.base_url + '/rss/rss.xml', 'test'
        )

    await fetch_news_async(module, 0, 0)

    articles = await models.Article.all().order_by(
        'article_id'
    ).prefetch_related('tags')
    assert len(articles) == 2

    article1 = articles[0]
    assert article1.slug_name == (
        f'{app.base_url}/news/million-bucks'
    )
    assert article1.title == 'Любовь на миллион'
    assert article1.date.isoformat() == '2022-07-03T06:11:11+00:00'
    assert len(article1.tags) == 1
    assert article1.tags[0].title == 'Лента новостей'


# TODO: test other methods
