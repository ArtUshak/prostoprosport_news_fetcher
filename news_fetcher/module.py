"""Base class for source modules."""
import abc
from typing import Dict, Iterable, List, Optional, Set, Tuple

import aiohttp
import tortoise

import models


class SourceModule(abc.ABC):
    """Base class for source modules."""

    source_slug_name: str

    @abc.abstractmethod
    async def fetch_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> Tuple[Iterable[models.Article], Dict[str, Set[str]]]:
        """
        Fetch news articles without acutally inserting them into database.

        Return tuple. First item should be iterable of article models.
        Second item should be dictionary mapping from slug names to sets of tag
        titles.
        """
        raise NotImplementedError()

    async def insert_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> None:
        articles, tag_titles_by_slug_name = await self.fetch_news(
            session, page, source
        )
        tag_titles: Set[str]
        if len(tag_titles_by_slug_name) != 0:
            tag_titles = set.union(*tag_titles_by_slug_name.values())
        else:
            tag_titles = set()
        async with tortoise.transactions.in_transaction():
            await models.Tag.bulk_create(
                map(lambda title: models.Tag(title=title), tag_titles),
                ignore_conflicts=True
            )
            tags_by_title = await models.Tag.in_bulk(tag_titles, 'title')
            await models.Article.bulk_create(
                articles, ignore_conflicts=True
            )
            articles_by_slug_name = await models.Article.filter(
                source=source
            ).in_bulk(tag_titles_by_slug_name.keys(), 'slug_name')
            article_tags: List[models.ArticleTag] = []
            for slug_name, tag_titles in tag_titles_by_slug_name.items():
                if slug_name not in articles_by_slug_name:
                    continue
                for tag_title in tag_titles:
                    article_tags.append(
                        models.ArticleTag(
                            tag_id=tags_by_title[tag_title].tag_id,
                            article_id=articles_by_slug_name[
                                slug_name
                            ].article_id
                        )
                    )
            await models.ArticleTag.bulk_create(
                article_tags, ignore_conflicts=True
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
        """Fetch article text and save it in database."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_wiki_page_text(
        self, article: models.Article, bot_name: str
    ) -> Optional[str]:
        """Get wiki-page text for article from wiki-text paragraphs."""
        raise NotImplementedError()
