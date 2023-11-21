"""Module to fetch news from ProstoProSport."""
import dataclasses
import datetime
import json
import urllib
from typing import Dict, Iterable, List, Optional, Set, TextIO, Tuple, Union

import aiohttp
import bs4
import click

import models
from module import SourceModule
from utils import (check_dict_str_str, check_int, check_list_dict_str_object,
                   check_list_str, check_str)
from wikitext import html_to_wikitext

PROSTOPROSPORT_API_NEWS_URL = 'https://api.prostoprosport.ru/api/news/'
PROSTOPROSPORT_API_MAIN_NEWS_URL = (
    'https://api.prostoprosport.ru/api/main_news/'
)
PROSTOPROSPORT_WEBSITE_URL = 'https://prostoprosport.ru'


def load_category_urls(elements: List[Dict[str, object]]) -> Iterable[str]:
    """Load category URLs from dictionary recursively and iterate over them."""
    for element in elements:
        if 'url' in element:
            yield check_str(element['url'])
        if 'child' in element:
            child = check_list_dict_str_object(element['child'])
            for url in load_category_urls(child):
                yield url


def get_categories(data: object) -> Tuple[Dict[int, str], Dict[str, str]]:
    """Get categories_by_slug dictionary from data loaded from JSON."""
    if not isinstance(data, dict):
        raise TypeError(data)
    categories_by_id_data = data['categories_by_id']
    if not isinstance(categories_by_id_data, dict):
        raise TypeError(categories_by_id_data)
    categories_by_id: Dict[int, str] = {}
    for key, value in categories_by_id_data.items():
        if not isinstance(key, str):
            raise TypeError(key)
        if not isinstance(value, str):
            raise TypeError(value)
        categories_by_id[int(key)] = value
    categories_by_slug: Dict[str, str] = check_dict_str_str(
        data['categories_by_slug']
    )
    return categories_by_id, categories_by_slug


@dataclasses.dataclass
class ProstoprosportMiscData:
    category_id: int
    category_slug: str
    category_title: str

    def to_json_dict(
        self
    ) -> Dict[str, Union[str, int]]:
        """Return dictionary to save to JSON."""
        return {
            'category_id': self.category_id,
            'category_slug': self.category_slug,
            'category_title': self.category_title
        }

    @staticmethod
    def from_json_dict(
        data: object
    ) -> 'ProstoprosportMiscData':
        """Create news item from dictionary loaded from JSON."""
        if not isinstance(data, dict):
            raise TypeError(data)
        category_slug = check_str(data['category_slug'])
        category_id = check_int(data['category_id'])
        category_title = check_str(data['category_title'])
        return ProstoprosportMiscData(
            category_id, category_slug, category_title
        )

    def get_page_url(
        self,
        slug_name: str,
        categories_by_id: Dict[int, str],
        categories_by_slug: Dict[str, str]
    ) -> Optional[str]:
        """Return page URL on website using URL dictionaries."""
        category_url: Optional[str] = None

        if self.category_slug in categories_by_slug:
            category_url = categories_by_slug[self.category_slug]
        elif self.category_id in categories_by_id:
            category_color = categories_by_id[self.category_id]
            if category_color == self.category_slug:
                category_url = category_color
            else:
                category_url = category_color + '/' + self.category_slug
        else:
            category_url = 'post'

        return (
            f'{PROSTOPROSPORT_WEBSITE_URL}/{category_url}/{slug_name}'
        )


def get_api_url(api_method: Optional[str]) -> str:
    if api_method == 'news':
        return PROSTOPROSPORT_API_NEWS_URL
    else:
        return PROSTOPROSPORT_API_MAIN_NEWS_URL


class ProstoprosportModule(SourceModule):
    source_slug_name = 'prostoprosport'
    api_url: str
    categories_by_id: Dict[int, str]
    categories_by_slug: Dict[str, str]

    def __init__(
        self, categories_file: Optional[TextIO], api_method: Optional[str]
    ):
        if categories_file is None:
            self.categories_by_id = {}
            self.categories_by_slug = {}
        else:
            categories_data = json.load(categories_file)
            self.categories_by_id, self.categories_by_slug = get_categories(
                categories_data
            )
        self.api_url = get_api_url(api_method)

    async def fetch_news(
        self, session: aiohttp.ClientSession, page: int, source: models.Source
    ) -> Tuple[Iterable[models.Article], Dict[str, Set[str]]]:
        params = {
            'offset': 1,
            'page': page
        }
        async with session.get(self.api_url, params=params) as response:
            data = await response.json()

        tag_titles_by_slug_name: Dict[str, Set[str]] = {}

        articles: List[models.Article] = []
        for element in data:
            title_str = element['post_title']
            if not isinstance(title_str, str):
                raise ValueError()
            name_str = element['post_name']
            if not isinstance(name_str, str):
                raise ValueError()
            date_str = element['post_date'][:-1]
            if not isinstance(date_str, str):
                raise ValueError()
            tags_str = element['tax']
            if not isinstance(tags_str, str):
                raise ValueError()
            date = datetime.datetime.fromisoformat(date_str)

            tags = json.loads('[' + tags_str + ']')
            category_id: Optional[int] = None
            category_slug: Optional[str] = None
            category_title: Optional[str] = None
            tag_titles: List[str] = []
            for tag in tags:
                if 'category' in tag:
                    category_id = int(tag['category']['id'])
                    category_slug = tag['category']['slug']
                    category_title = tag['category']['name']
                elif 'post_tag' in tag:
                    tag_titles.append(tag['post_tag']['name'])
            if len(tag_titles_by_slug_name) != 0:
                tag_titles_by_slug_name[name_str] = set(filter(
                    bool, tag_titles
                ))

            if category_id is None:
                raise ValueError()
            if category_slug is None:
                raise ValueError()
            if category_title is None:
                raise ValueError()

            misc_data = ProstoprosportMiscData(
                category_id, category_slug, category_title
            )

            articles.append(models.Article(
                source=source, slug_name=name_str,
                date=date, title=title_str,
                source_url=misc_data.get_page_url(
                    name_str, self.categories_by_id, self.categories_by_slug
                )
            ))

        return articles, tag_titles_by_slug_name

    async def fetch_article(
        self, article: models.Article, session: aiohttp.ClientSession
    ) -> None:
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

        author_tags = parser.select('.author > form > button')
        author_name: Optional[str] = None
        if len(author_tags) >= 1:
            author_name = author_tags[0].text
        paragraph_tags = parser.select('.page-content > article > p')
        wikitext_paragraphs: List[str] = []
        for paragraph_tag in paragraph_tags:
            wikitext = html_to_wikitext(
                paragraph_tag,
                lambda href:
                urllib.parse.urljoin(href, PROSTOPROSPORT_WEBSITE_URL)
            )
            wikitext_paragraphs.append(wikitext)

        if author_name is not None:
            article.author_name = author_name
        article.wikitext_paragraphs = wikitext_paragraphs
        await article.save()

    async def get_wiki_page_text(
        self, article: models.Article, bot_name: str
    ) -> Optional[str]:
        if article.wikitext_paragraphs is None:
            return None
        try:
            wikitext_paragraphs = check_list_str(article.wikitext_paragraphs)
        except TypeError:
            return None  # TODO

        date_str = article.date.strftime('%Y-%m-%d')

        try:
            misc_data = ProstoprosportMiscData.from_json_dict(
                article.misc_data
            )
        except TypeError:
            return None
        except KeyError:
            return None

        tag_titles = sorted(map(
            lambda tag: tag.title, await article.tags.all()
        ))
        tag_titles_list: List[str]
        if misc_data.category_title is None:
            full_tag_titles = tag_titles
        else:
            full_tag_titles = [misc_data.category_title] + tag_titles
        tag_titles_str = '|'.join(full_tag_titles)
        wikitext_elements: List[str] = []

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
            f'{{{{Prostoprosport.ru|{template_parameters_str}}}}}'
        )
        wikitext_elements.append(
            f'{{{{Загружено ботом|{bot_name}|Prostoprosport.ru}}}}'
        )
        wikitext_elements.append('{{Подвал новости}}')
        wikitext_elements.append(f'{{{{Категории|{tag_titles_str}}}}}')

        return '\n\n'.join(wikitext_elements)


@click.group()
def cli() -> None:
    pass


@click.command()
@click.option(
    '--input-from-js-file',
    type=click.File(mode='rt'),
    default='data/categories_from_js.json',
    help='JSON file with categories_by_slug data grabbed from JavaScript'
)
@click.option(
    '--input-bonus-file',
    type=click.File(mode='rt'),
    default='data/categories_bonus.json',
    help='JSON file with additional data'
)
@click.option(
    '--input-colors-file',
    type=click.File(mode='rt'),
    default='data/category_colors.json',
    help='JSON file with category color data'
)
@click.option(
    '--output-file',
    type=click.File(mode='wt'),
    default='data1/categories_data.json',
    help='Output JSON file'
)
def prostoprosport_process_categories(
    input_from_js_file: TextIO, input_bonus_file: TextIO,
    input_colors_file: TextIO, output_file: TextIO,
) -> None:
    """Build categories_by_slug list from file."""
    categories_data_from_js = json.load(input_from_js_file)
    categories_data_bonus = json.load(input_bonus_file)
    categories_data_colors = json.load(input_colors_file)

    categories_by_slug: Dict[str, str] = {}
    for category_url_data in load_category_urls(categories_data_from_js):
        category_url = check_str(category_url_data)
        category_slug = category_url.split('/')[-1]
        categories_by_slug[category_slug] = '/'.join(
            category_url.split('/')[2:]
        )
    for category_url_data in categories_data_bonus:
        category_url = check_str(category_url_data)
        category_slug = category_url.split('/')[-1]
        categories_by_slug[category_slug] = category_url

    categories_by_id_data: Dict[int, str] = {}
    for category_color_data, category_ids in categories_data_colors.items():
        category_color = check_str(category_color_data)
        for category_id_data in category_ids:
            category_id = check_int(category_id_data)
            categories_by_id_data[category_id] = category_color

    data = {
        'categories_by_id': categories_by_id_data,
        'categories_by_slug': categories_by_slug
    }
    json.dump(data, output_file, indent=4)


if __name__ == '__main__':
    cli()
