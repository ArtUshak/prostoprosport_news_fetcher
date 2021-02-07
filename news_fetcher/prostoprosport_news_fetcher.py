"""Script to fetch news using RSS and convert to wiki-text."""
import dataclasses
import datetime
import json
import sys
from typing import Any, Dict, Iterable, List, Optional, TextIO, Union

import click
import requests

PROSTOPROSPORT_API_NEWS_URL = 'https://api.prostoprosport.ru/api/main_news/'
PROSTOPROSPORT_WEBSITE_URL = 'https://prostoprosport.ru'


def check_str(data: Any) -> str:
    """Check if data is `str` and return it."""
    if not isinstance(data, str):
        raise TypeError(data)
    return data


def check_optional_str(data: Any) -> Optional[str]:
    """Check if data is `Optional[str]` and return it."""
    if data is None:
        return None
    if not isinstance(data, str):
        raise TypeError(data)
    return data


def check_bool(data: Any) -> bool:
    """Check if data is `bool` and return it."""
    if not isinstance(data, bool):
        raise TypeError(data)
    return data


def check_dict_str_str(data: Any) -> Dict[str, str]:
    """Check if data is `Dict[str, str]` and return it."""
    if not isinstance(data, dict):
        raise TypeError(data)
    for key, value in data.items():
        if not isinstance(key, str):
            raise TypeError(key)
        if not isinstance(value, str):
            raise TypeError(value)
    return data


@dataclasses.dataclass
class NewsItem:
    """News item fetched through API."""

    name: str
    title: str
    category_slug: str
    date: datetime.datetime
    url: Optional[str]
    url_ok: Optional[bool] = None

    @staticmethod
    def initialize(
        name: str, title: str, category_slug: str,
        date: datetime.datetime, categories: Dict[str, str]
    ) -> 'NewsItem':
        """Create news item data."""
        result = NewsItem(name, title, category_slug, date, None, None)
        result.get_page_url(categories)
        return result

    def get_page_url(self, categories: Dict[str, str]) -> Optional[str]:
        """Return page URL on website using categories URL dictionary."""
        if self.category_slug not in categories:
            return None
        category_url = categories[self.category_slug]
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
        self.url_ok = None
        return self.url_ok

    def to_json_dict(self) -> Dict[str, Union[bool, Optional[str]]]:
        """Return dictionary to save to JSON."""
        data: Dict[str, Union[bool, Optional[str]]] = {
            'name': self.name,
            'title': self.title,
            'category_slug': self.category_slug,
            'date': self.date.isoformat(),
            'url': self.url
        }
        if self.url_ok is not None:
            data['url_ok'] = self.url_ok
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
        date_str = check_str(data['date'])
        date = datetime.datetime.fromisoformat(date_str)
        url = check_optional_str(data['url'])
        url_ok: Optional[bool] = None
        if 'url_ok' in data:
            url_ok = check_bool(data['url_ok'])
        return NewsItem(name, title, category_slug, date, url, url_ok)


def get_news_items(data: Any) -> Iterable[NewsItem]:
    """Load news items from data and iterate over them."""
    if not isinstance(data, Iterable):
        raise TypeError(data)
    return map(NewsItem.from_json_dict, data)


def iterate_news(
    session: requests.Session, page: int, categories: Dict[str, str]
) -> Iterable[NewsItem]:
    """Fetch news items using API and iterate over them."""
    params = {
        'offset': 1,
        'page': page
    }
    r = session.get(PROSTOPROSPORT_API_NEWS_URL, params=params)
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
        category_slug: Optional[str] = None
        for tag in tags:
            if 'category' in tag:
                category_slug = tag['category']['slug']
                break
        if category_slug is None:
            raise ValueError()
        yield NewsItem.initialize(
            name_str, title_str, category_slug, date, categories
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
    help='JSON file with categories data grabbed from JavaScript'
)
@click.option(
    '--input-bonus-file',
    type=click.File(mode='rt'),
    default='data/categories_bonus.json',
    help='JSON file with additional data'
)
@click.option(
    '--output-file',
    type=click.File(mode='wt'),
    default='data/categories.json',
    help='Output JSON file'
)
def process_categories(
    input_from_js_file: TextIO, input_bonus_file: TextIO,
    output_file: TextIO
) -> None:
    """Build categories list from file."""
    categories_data_from_js = json.load(input_from_js_file)
    categories_data_bonus = json.load(input_bonus_file)
    categories: Dict[str, str] = {}
    for category_url in load_category_urls(categories_data_from_js):
        category_slug = category_url.split('/')[-1]
        categories[category_slug] = '/'.join(category_url.split('/')[2:])
    for category_url in categories_data_bonus:
        category_slug = category_url.split('/')[-1]
        categories[category_slug] = category_url
    json.dump(categories, output_file, indent=4)


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
    default='data/categories.json',
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
def fetch_news(
    first_page: int, last_page: int, categories_file: TextIO,
    output_file: TextIO, check_url: bool
) -> None:
    """
    Fetch news from Prostoprosport.ru using API.

    Page numbers are from most recent (1) to least recent.
    Results are retrieved from least recent to first recent.
    """
    categories_data = json.load(categories_file)

    categories = check_dict_str_str(categories_data)

    session = requests.Session()
    items: List[NewsItem] = []
    for page in range(first_page, last_page + 1):
        for item in list(iterate_news(session, page, categories)):
            items.append(item)
    items.sort(key=lambda item: item.date)

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


cli.add_command(process_categories)
cli.add_command(fetch_news)
cli.add_command(filter_fetched_news)


if __name__ == '__main__':
    cli()
