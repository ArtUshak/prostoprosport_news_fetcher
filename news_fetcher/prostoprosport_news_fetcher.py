"""Script to fetch news using RSS and convert to wiki-text."""
import dataclasses
import datetime
import json
import pathlib
import sys
from typing import Any, Dict, Iterable, List, Optional, TextIO, Tuple, Union

import bs4
import click
import requests

from utils import (check_bool, check_dict_str_str, check_int, check_list_str,
                   check_optional_str, check_str, html_to_wikitext)

PROSTOPROSPORT_API_NEWS_URL = 'https://api.prostoprosport.ru/api/news/'
PROSTOPROSPORT_API_MAIN_NEWS_URL = (
    'https://api.prostoprosport.ru/api/main_news/'
)
PROSTOPROSPORT_WEBSITE_URL = 'https://prostoprosport.ru'


def get_categories(data: Any) -> Tuple[Dict[int, str], Dict[str, str]]:
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
class NewsItem:
    """News item fetched through API."""

    name: str
    title: str
    category_id: int
    category_slug: str
    category_title: Optional[str]
    date: datetime.datetime
    tag_titles: List[str]
    author_name: Optional[str]
    url: Optional[str]
    url_ok: Optional[bool] = None
    wikitext_paragraphs: Optional[List[str]] = None

    @staticmethod
    def initialize(
        name: str, title: str,
        category_id: int, category_slug: str, category_title: str,
        date: datetime.datetime, categories_by_id: Dict[int, str],
        categories_by_slug: Dict[str, str], tag_titles: List[str]
    ) -> 'NewsItem':
        """Create news item data."""
        result = NewsItem(
            name, title, category_id, category_slug, category_title,
            date, tag_titles, None, None, None, None
        )
        result.get_page_url(categories_by_id, categories_by_slug)
        return result

    def get_page_url(
        self,
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

        self.url = (
            f'{PROSTOPROSPORT_WEBSITE_URL}/{category_url}/{self.name}'
        )
        return self.url

    def check_url(self, session: requests.Session) -> Optional[bool]:
        """
        Check if URL is valid, return result and save it.

        Result is `None` if URL is undefined, `True` if URL is correct
        (HEAD request returns 200), `False` otherwise.
        """
        if self.url is not None:
            url_ok: bool = True
            try:
                r1 = session.head(self.url)
            except requests.exceptions.RequestException:
                url_ok = False
            else:
                if r1.status_code != 200:
                    url_ok = False
            self.url_ok = url_ok
        else:
            self.url_ok = None
        return self.url_ok

    def fetch_article(
        self, session: requests.Session
    ) -> Tuple[Optional[str], List[str]]:
        """
        Fetch article text.

        Return tuple of text as list of wiki-text paragraphs and author name,
        save it.
        """
        if self.url is None:
            raise ValueError()
        r = session.get(self.url)
        if r.status_code != 200:
            raise ValueError()
        parser = bs4.BeautifulSoup(markup=r.text, features='html.parser')
        author_tags = parser.select('.author > form > button')
        author_name: Optional[str] = None
        if len(author_tags) >= 1:
            author_name = author_tags[0].text
        paragraph_tags = parser.select('.page-content > article > p')
        wikitext_paragraphs: List[str] = []
        for paragraph_tag in paragraph_tags:
            wikitext = html_to_wikitext(paragraph_tag)
            wikitext_paragraphs.append(wikitext)
        self.author_name = author_name
        self.wikitext_paragraphs = wikitext_paragraphs
        return self.author_name, self.wikitext_paragraphs

    def get_wiki_page_text(self, bot_name: str) -> str:
        """Get wiki-page text for article from wiki-text paragraphs."""
        if self.wikitext_paragraphs is None:
            raise ValueError()
        wikitext_elements: List[str] = []
        date_str = self.date.strftime('%Y-%m-%d')
        tag_titles_list: List[str]
        if self.category_title is None:
            full_tag_titles = self.tag_titles
        else:
            full_tag_titles = [self.category_title] + self.tag_titles
        tag_titles_str = '|'.join(full_tag_titles)
        wikitext_elements.append(f'{{{{дата|{date_str}}}}}')
        wikitext_elements.append(f'{{{{тема|{tag_titles_str}}}}}')
        wikitext_elements += self.wikitext_paragraphs
        wikitext_elements.append('{{-}}')
        wikitext_elements.append('== Источники ==')
        template_parameters = [f'url={self.url}', f'title={self.title}']
        if self.author_name is not None:
            template_parameters.append(f'author={self.author_name}')
        template_parameters_str = '|'.join(template_parameters)
        wikitext_elements.append(
            f'{{{{Prostoprosport.ru|{template_parameters_str}}}}}'
        )
        wikitext_elements.append(
            f'{{{{Загружено ботом в архив|{bot_name}|Prostoprosport.ru}}}}'
        )
        wikitext_elements.append('{{Подвал новости}}')
        wikitext_elements.append(f'{{{{Категории|{tag_titles_str}}}}}')
        return '\n\n'.join(wikitext_elements)

    def to_json_dict(
        self
    ) -> Dict[str, Union[bool, str, int, List[str], None]]:
        """Return dictionary to save to JSON."""
        data: Dict[str, Union[bool, str, int, List[str], None]] = {
            'name': self.name,
            'title': self.title,
            'category_id': self.category_id,
            'category_slug': self.category_slug,
            'category_title': self.category_title,
            'date': self.date.isoformat(),
            'url': self.url,
            'tag_titles': self.tag_titles
        }
        if self.author_name is not None:
            data['author_name'] = self.author_name
        if self.url_ok is not None:
            data['url_ok'] = self.url_ok
        if self.wikitext_paragraphs is not None:
            data['wikitext_paragraphs'] = self.wikitext_paragraphs
        return data

    @staticmethod
    def from_json_dict(
        data: Any
    ) -> 'NewsItem':
        """Create news item from dictionary loaded from JSON."""
        if not isinstance(data, dict):
            raise TypeError(data)
        name = check_str(data['name'])
        title = check_str(data['title'])
        category_slug = check_str(data['category_slug'])
        category_id = check_int(data['category_id'])
        category_title: Optional[str] = None
        if 'category_title' in data:
            category_title = check_str(data['category_title'])
        date_str = check_str(data['date'])
        date = datetime.datetime.fromisoformat(date_str)
        url = check_optional_str(data['url'])
        url_ok: Optional[bool] = None
        if 'url_ok' in data:
            url_ok = check_bool(data['url_ok'])
        wikitext_paragraphs: Optional[List[str]] = None
        if 'wikitext_paragraphs' in data:
            wikitext_paragraphs = check_list_str(data['wikitext_paragraphs'])
        tag_titles: List[str] = []
        if 'tag_titles' in data:
            tag_titles = check_list_str(data['tag_titles'])
        author_name: Optional[str] = None
        if 'author_name' in data:
            author_name = check_str(data['author_name'])
        return NewsItem(
            name, title, category_id, category_slug, category_title, date,
            tag_titles, author_name, url, url_ok, wikitext_paragraphs
        )


def get_news_items(data: Any) -> Iterable[NewsItem]:
    """Load news items from data and iterate over them."""
    if not isinstance(data, Iterable):
        raise TypeError(data)
    return map(NewsItem.from_json_dict, data)


def iterate_news(
    session: requests.Session, page: int, categories_by_id: Dict[int, str],
    categories_by_slug: Dict[str, str], api_url: str
) -> Iterable[NewsItem]:
    """Fetch news items using API and iterate over them."""
    params = {
        'offset': 1,
        'page': page
    }
    r = session.get(api_url, params=params)
    data = r.json()
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
        if category_id is None:
            raise ValueError()
        if category_slug is None:
            raise ValueError()
        if category_title is None:
            raise ValueError()
        yield NewsItem.initialize(
            name_str, title_str, category_id, category_slug, category_title,
            date, categories_by_id, categories_by_slug, tag_titles
        )


def load_category_urls(elements: List[Dict[str, Any]]) -> Iterable[str]:
    """Load category URLs from dictionary recursively and iterate over them."""
    for element in elements:
        if 'url' in element:
            yield element['url']
        if 'child' in element:
            for url in load_category_urls(element['child']):
                yield url


@click.group()
def cli() -> None:
    """Command line."""
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
def process_categories(
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


@click.command()
@click.option(
    '--first-page', type=click.IntRange(min=1), default=1,
    help='Number of first page to load, should be not less than 1'
)
@click.option(
    '--last-page', type=click.IntRange(min=1), default=1,
    help='Number of last page to load, should be not less than 1'
)
@click.option(
    '--categories-file',
    type=click.File(mode='rt'),
    help='File to read categories URLs from'
)
@click.option(
    '--output-file', default=sys.stdout, type=click.File(mode='wt'),
    help='Output JSON file'
)
@click.option(
    '--check-url/--no-check-url', default=False,
    help='Check URLs using HEAD requests'
)
@click.option(
    '--api-method', default='main_news',
    type=click.Choice(['main_news', 'news']),
    help='API method to use: main_news or news'
)
def fetch_news(
    first_page: int, last_page: int,
    categories_file: Optional[TextIO],
    output_file: TextIO, check_url: bool, api_method: str
) -> None:
    """
    Fetch news from Prostoprosport.ru using API.

    Page numbers are from most recent (1) to least recent.
    Results are retrieved from least recent to first recent.
    """
    categories_by_id: Dict[int, str]
    categories_by_slug: Dict[str, str]
    if categories_file is None:
        categories_by_id = {}
        categories_by_slug = {}
    else:
        categories_data = json.load(categories_file)
        categories_by_id, categories_by_slug = get_categories(categories_data)

    session = requests.Session()
    api_url: str
    if api_method == 'news':
        api_url = PROSTOPROSPORT_API_NEWS_URL
    else:
        api_url = PROSTOPROSPORT_API_MAIN_NEWS_URL
    items: List[NewsItem] = []
    with click.progressbar(
        range(first_page, last_page + 1), length=(last_page + 1 - first_page)
    ) as bar1:
        for page in bar1:
            for item in list(
                iterate_news(
                    session, page, categories_by_id, categories_by_slug,
                    api_url
                )
            ):
                items.append(item)
    items.sort(key=lambda item: item.date)
    if check_url:
        with click.progressbar(items) as bar2:
            for item in bar2:
                item.check_url(session)

    data = list(map(lambda item: item.to_json_dict(), items))
    json.dump(data, output_file, ensure_ascii=False, indent=4)


@click.command()
@click.option(
    '--date', type=click.DateTime(formats=['%Y-%m-%d']),
    help='Date to filter news by'
)
@click.option(
    '--input-file', default=sys.stdin, type=click.File(mode='rt'),
    help='Input JSON file'
)
@click.option(
    '--output-file', default=sys.stdout, type=click.File(mode='wt'),
    help='Output JSON file'
)
def filter_fetched_news(
    date: Optional[datetime.datetime], input_file: TextIO, output_file: TextIO
) -> None:
    """Filter fetched news by date."""
    data = json.load(input_file)

    items: Iterable[NewsItem] = get_news_items(data)
    if date is not None:
        date_date = date.date()
        items = filter(lambda item: item.date.date() == date_date, items)

    items_data = list(map(lambda item: item.to_json_dict(), items))
    json.dump(items_data, output_file, ensure_ascii=False, indent=4)


@click.command()
@click.option(
    '--input-file', default=sys.stdin, type=click.File(mode='rt'),
    help='Input JSON file'
)
@click.option(
    '--output-file', default=sys.stdout, type=click.File(mode='wt'),
    help='Output JSON file'
)
def fetch_news_pages(
    input_file: TextIO, output_file: TextIO
) -> None:
    """Fetch articles for news."""
    data = json.load(input_file)

    session = requests.Session()
    items: List[NewsItem] = list(get_news_items(data))
    with click.progressbar(items) as bar:
        for item in bar:
            item.fetch_article(session)

    items_data = list(map(lambda item: item.to_json_dict(), items))
    json.dump(items_data, output_file, ensure_ascii=False, indent=4)


@click.command()
@click.option(
    '--input-file', default=sys.stdin, type=click.File(mode='rt'),
    help='Input JSON file'
)
@click.option(
    '--output-file', default=sys.stdout, type=click.File(mode='wt'),
    help='Output list JSON file'
)
@click.option(
    '--output-directory', default='data1/pages',
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help='Output list JSON file'
)
@click.option(
    '--bot-name', default='NewsBot', type=click.STRING
)
def generate_wiki_pages(
    input_file: TextIO, output_file: TextIO, output_directory: str,
    bot_name: str
) -> None:
    """Generate wiki-pages for news articles."""
    data = json.load(input_file)

    output_directory_path = pathlib.Path(output_directory)

    pages: Dict[str, str] = {}

    items: List[NewsItem] = list(get_news_items(data))
    with click.progressbar(items) as bar:
        for item in bar:
            page_file_path = output_directory_path.joinpath(f'{item.name}.txt')
            with open(page_file_path, mode='wt') as page_file:
                page_file.write(item.get_wiki_page_text(bot_name))
            pages[item.title] = str(page_file_path)

    json.dump(pages, output_file, ensure_ascii=False, indent=4)


cli.add_command(process_categories)
cli.add_command(fetch_news)
cli.add_command(filter_fetched_news)
cli.add_command(fetch_news_pages)
cli.add_command(generate_wiki_pages)


if __name__ == '__main__':
    cli()
