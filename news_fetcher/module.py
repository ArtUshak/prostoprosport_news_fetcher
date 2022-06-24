"""Base class for source modules."""
import abc
from typing import Iterable, Optional

import aiohttp
import tortoise

import models


class SourceModule(abc.ABC):
    """Base class for source modules."""
    source_slug_name: str

    @abc.abstractmethod
    async def fetch_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> Iterable[models.Article]:
        raise NotImplementedError()

    async def insert_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> None:
        articles = await self.fetch_news(
            session, page, source
        )
        async with tortoise.transactions.in_transaction():
            await models.Article.bulk_create(
                articles, ignore_conflicts=True
            )

    async def check_url(
        self, article: models.Article, session: aiohttp.ClientSession,
        force: bool = False
    ) -> None:
        """
        Check if URL is valid, write `url_ok` field and save model.

        Result is `True` if URL is correct (HEAD request returns 200),
        `False` otherwise.
        """
        if not force and article.source_url_ok is not None:
            return
        url_ok: bool = False
        try:
            async with session.head(article.source_url) as response:
                url_ok = response.status == 200
        except aiohttp.client_exceptions.ClientError:
            pass
        article.source_url_ok = url_ok
        await article.save()

    @abc.abstractmethod
    async def fetch_article(
        self, article: models.Article, session: aiohttp.ClientSession
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_wiki_page_text(
        self, article: models.Article, bot_name: str
    ) -> Optional[str]:
        raise NotImplementedError()
