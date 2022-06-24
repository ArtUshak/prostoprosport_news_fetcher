import json
import urllib.parse
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Set, TextIO

import aiohttp
import bs4
import feedparser

import models
from module import SourceModule
from utils import (check_dict_str_object, check_list_str, check_str,
                   html_to_wikitext, struct_time_to_datetime)


def entry_to_json_dict(
    data: feedparser.util.FeedParserDict
) -> Dict[str, object]:
    tmp_dict = dict(data)
    if 'created_parsed' in data:
        tmp_dict['created_parsed'] = (
            struct_time_to_datetime(tmp_dict['created_parsed']).isoformat()
        )
    if 'expired_parsed' in data:
        tmp_dict['expired_parsed'] = (
            struct_time_to_datetime(tmp_dict['expired_parsed']).isoformat()
        )
    if 'published_parsed' in data:
        tmp_dict['published_parsed'] = (
            struct_time_to_datetime(tmp_dict['published_parsed']).isoformat()
        )
    if 'updated_parsed' in data:
        tmp_dict['updated_parsed'] = (
            struct_time_to_datetime(tmp_dict['updated_parsed']).isoformat()
        )
    return tmp_dict


class RSSModule(SourceModule):
    rss_url: str
    paragraph_selector: str
    source_title: str
    css_selector: str
    replaceable_netlocs: Set[str]

    def __init__(
        self, config_file: TextIO, rss_url: str, source_slug_name: str
    ):
        self.rss_url = rss_url
        self.source_slug_name = source_slug_name
        config_data = check_dict_str_object(json.load(config_file))
        self.source_title = check_str(config_data.get('source_title'))
        self.css_selector = check_str(config_data.get('css_selector'))
        self.replaceable_netlocs = set(
            check_list_str(config_data.get('replaceable_netlocs'))
        )

    async def fetch_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> Iterable[models.Article]:
        # TODO: page is ignored: maybe should warn about it
        articles: List[models.Article] = []

        async with session.get(self.rss_url) as response:
            text = await response.read()
            parsed_feed = feedparser.parse(BytesIO(text))
            for element in parsed_feed.entries:
                author_name: Optional[str] = None
                if 'author' in element:
                    author_name = element.author
                # TODO: write tags
                articles.append(models.Article(
                    source=source,
                    slug_name=element.link,  # TODO
                    title=element.title,
                    source_url=element.link,
                    date=struct_time_to_datetime(element.published_parsed),
                    author_name=author_name,
                    misc_data=entry_to_json_dict(element)  # TODO
                ))

        return articles

    def handle_link(
        self, base_url: urllib.parse.ParseResult, href: str
    ) -> str:
        href_parsed = urllib.parse.urlparse(href)
        if (
            (not href_parsed.netloc)
            or (href_parsed.netloc in self.replaceable_netlocs)
        ):
            return href_parsed._replace(
                scheme=base_url.scheme, netloc=base_url.netloc
            ).geturl()
        return href

    async def fetch_article(
        self, article: models.Article, session: aiohttp.ClientSession
    ) -> None:
        """
        Fetch article text and save it in database.
        """
        if not article.source_url_ok:
            return  # TODO

        async with session.get(article.source_url) as response:
            if response.status == 404:
                article.source_url_ok = False
                return
            if response.status != 200:
                raise ValueError(response.status)
            parser = bs4.BeautifulSoup(
                markup=await response.text(), features='html.parser'
            )

        paragraph_tags = parser.select(self.css_selector)
        wikitext_paragraphs: List[str] = []

        base_url = urllib.parse.urlparse(article.source_url)._replace(
            path='', query='', fragment=''
        )

        for paragraph_tag in paragraph_tags:
            wikitext = html_to_wikitext(
                paragraph_tag, lambda href: self.handle_link(base_url, href)
            )
            wikitext_paragraphs.append(wikitext)

        article.wikitext_paragraphs = wikitext_paragraphs
        await article.save()

    async def get_wiki_page_text(
        self, article: models.Article, bot_name: str
    ) -> Optional[str]:
        """Get wiki-page text for article from wiki-text paragraphs."""
        if article.wikitext_paragraphs is None:
            return None
        try:
            wikitext_paragraphs = check_list_str(article.wikitext_paragraphs)
        except TypeError:
            return None  # TODO

        date_str = article.date.strftime('%Y-%m-%d')

        tag_titles = sorted(map(
            lambda tag: tag.title, await article.tags.all()
        ))
        tag_titles_str = '|'.join(tag_titles)
        wikitext_elements: List[str] = []

        wikitext_elements.append(f'{{{{дата|{date_str}}}}}')
        wikitext_elements.append(f'{{{{тема|{tag_titles_str}}}}}')
        wikitext_elements += wikitext_paragraphs
        wikitext_elements.append('{{-}}')
        wikitext_elements.append('== Источники ==')

        template_parameters = [
            f'url={article.source_url}', f'title={article.title}'
        ]
        if article.author_name is not None:
            template_parameters.append(f'author={article.author_name}')
        template_parameters_str = '|'.join(template_parameters)

        wikitext_elements.append(
            f'{{{{Prostoprosport.ru|{template_parameters_str}}}}}'
        )
        wikitext_elements.append(
            f'{{{{Загружено ботом в архив|{bot_name}|{self.source_title}}}}}'
        )
        wikitext_elements.append('{{Подвал новости}}')
        wikitext_elements.append(f'{{{{Категории|{tag_titles_str}}}}}')

        return '\n\n'.join(wikitext_elements)
