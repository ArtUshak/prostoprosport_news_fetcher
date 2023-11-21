import json
import urllib.parse
from io import BytesIO
from typing import (Dict, FrozenSet, Iterable, List, Optional, Set, TextIO,
                    Tuple)

import aiohttp
import bs4
import feedparser

import models
from module import SourceModule
from utils import (check_bool, check_dict_str_object, check_int,
                   check_list_str, check_optional_str, check_str,
                   struct_time_to_datetime)
from wikitext import html_to_wikitext


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
    source_title: str
    css_selector: str
    replaceable_netlocs: FrozenSet[str]
    default_categories: FrozenSet[str]
    removed_last_lines: int
    disable_bold_font: bool
    extra_first_lines: List[str]

    def __init__(
        self, config_file: TextIO, rss_url: str, source_slug_name: str
    ):
        self.rss_url = rss_url
        self.source_slug_name = source_slug_name
        config_data = check_dict_str_object(json.load(config_file))
        self.source_title = check_str(config_data.get('source_title'))
        self.css_selector = check_str(config_data.get('css_selector'))
        self.source_template_name = (
            check_optional_str(config_data.get('source_template_name'))
            or self.source_title
        )
        self.replaceable_netlocs = frozenset(
            check_list_str(config_data.get('replaceable_netlocs'))
        )
        if 'default_categories' in config_data:
            self.default_categories = frozenset(check_list_str(
                config_data['default_categories']
            ))
        else:
            self.default_categories = frozenset()
        if 'removed_last_lines' in config_data:
            self.removed_last_lines = check_int(
                config_data['removed_last_lines']
            )
        else:
            self.removed_last_lines = 0
        if 'disable_bold_font' in config_data:
            self.disable_bold_font = check_bool(
                config_data['disable_bold_font']
            )
        else:
            self.disable_bold_font = False
        if 'extra_first_lines' in config_data:
            self.extra_first_lines = check_list_str(
                config_data['extra_first_lines']
            )
        else:
            self.extra_first_lines = []

    async def fetch_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> Tuple[Iterable[models.Article], Dict[str, Set[str]]]:
        # TODO: page is ignored: maybe should warn about it
        articles: List[models.Article] = []
        tag_titles_by_slug_name: Dict[str, Set[str]] = {}

        async with session.get(self.rss_url) as response:
            text = await response.read()
            parsed_feed = feedparser.parse(BytesIO(text))
            for element in parsed_feed.entries:
                slug_name = element.link  # TODO
                author_name: Optional[str] = None
                if 'author' in element:
                    author_name = element.author
                tag_titles = set(self.default_categories)
                if 'tags' in element:
                    tag_titles = tag_titles.union(
                        set(filter(
                            bool,
                            map(lambda tag_data: tag_data.term, element.tags)
                        ))
                    )
                tag_titles_by_slug_name[slug_name] = tag_titles
                articles.append(models.Article(
                    source=source,
                    slug_name=slug_name,
                    title=element.title,
                    source_url=element.link,
                    date=struct_time_to_datetime(element.published_parsed),
                    author_name=author_name,
                    misc_data=entry_to_json_dict(element)  # TODO
                ))

        return articles, tag_titles_by_slug_name

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
                paragraph_tag, lambda href: self.handle_link(base_url, href),
                disable_bold_font=self.disable_bold_font
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

        if self.removed_last_lines > 0:
            wikitext_paragraphs = wikitext_paragraphs[
                :-self.removed_last_lines
            ]

        date_str = article.date.strftime('%Y-%m-%d')

        tag_titles = sorted(map(
            lambda tag: tag.title, await article.tags.all()
        ))
        tag_titles_str = '|'.join(tag_titles)
        wikitext_elements: List[str] = []

        wikitext_elements.extend(self.extra_first_lines)

        wikitext_elements.append(f'{{{{дата|{date_str}}}}}')
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
            f'{{{{{self.source_template_name}|{template_parameters_str}}}}}'
        )
        wikitext_elements.append(
            f'{{{{Загружено ботом|{bot_name}|{self.source_title}}}}}'
        )
        wikitext_elements.append('{{Подвал новости}}')
        wikitext_elements.append(f'{{{{Категории|{tag_titles_str}}}}}')

        return '\n\n'.join(wikitext_elements)
