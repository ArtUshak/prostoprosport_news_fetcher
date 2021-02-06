"""Script to fetch news using RSS and convert to wiki-text."""
import dataclasses
import datetime
import json
import sys
from typing import Any, Dict, Iterable, List, Optional, TextIO, Union

import click
import requests

PROSTOPROSPORT_API_NEWS_URL = 'https://api.prostoprosport.ru/api/main_news/'
PRSOTPROSPORT_WEBSITE_URL = 'https://prostoprosport.ru'


@click.group()
def cli() -> None:
    """Command line."""
    pass


@dataclasses.dataclass
class NewsItem:
    """News item fetched through API."""

    name: str
    title: str
    category_slug: str
    date: datetime.datetime

    def get_page_url(self, categories: Dict[str, str]) -> Optional[str]:
        """Return page URL on website using categories URL dictionary."""
        if self.category_slug not in categories:
            return None
        category_url = categories[self.category_slug]
        return (
            f'{PRSOTPROSPORT_WEBSITE_URL}/{category_url}/{self.name}'
        )

    def to_json_dict(self) -> Dict[str, Union[bool, Optional[str]]]:
        """Return dictionary to save to JSON."""
        return {
            'name': self.name,
            'title': self.title,
            'category_slug': self.category_slug,
            'date': self.date.isoformat()
        }


def iterate_news(session: requests.Session, page: int) -> Iterable[NewsItem]:
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
        yield NewsItem(name_str, title_str, category_slug, date)


def load_category_urls(elements: List[Dict[str, Any]]) -> Iterable[str]:
    """Load category URLs from dictionary recursively and iterate over them."""
    for element in elements:
        if 'url' in element:
            yield element['url']
        if 'child' in element:
            for url in load_category_urls(element['child']):
                yield url


@click.command()
@click.option(
    '--input-from-js-file-name',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    default='data/categories_from_js.json',
    help='JSON file with categories data grabbed from JavaScript'
)
@click.option(
    '--input-bonus-file-name',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    default='data/categories_bonus.json',
    help='JSON file with additional data'
)
@click.option(
    '--output-file-name',
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
    default='data/categories.json',
    help='Output JSON file'
)
def process_categories(
    input_from_js_file_name: str, input_bonus_file_name: str,
    output_file_name: str
) -> None:
    """Build categories list from file."""
    with open(input_from_js_file_name) as input_from_js_file:
        categories_data_from_js = json.load(input_from_js_file)
    with open(input_bonus_file_name) as input_bonus_file:
        categories_data_bonus = json.load(input_bonus_file)
    categories: Dict[str, str] = {}
    for category_url in load_category_urls(categories_data_from_js):
        category_slug = category_url.split('/')[-1]
        categories[category_slug] = '/'.join(category_url.split('/')[2:])
    for category_url in categories_data_bonus:
        category_slug = category_url.split('/')[-1]
        categories[category_slug] = category_url
    with open(output_file_name, 'wt') as output_file:
        json.dump(categories, output_file, indent=4)


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
    '--categories-file-name',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True
    ),
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
    first_page: int, last_page: int, categories_file_name: str,
    output_file: TextIO, check_url: bool
) -> None:
    """
    Fetch news from Prostoprosport.ru using API.

    Page numbers are from most recent (1) to least recent.
    Results are retrieved from least recent to first recent.
    """
    with open(categories_file_name) as categories_file:
        categories_data = json.load(categories_file)

    categories = check_dict_str_str(categories_data)

    session = requests.Session()
    data: List[Dict[str, Union[bool, Optional[str]]]] = []
    for page in range(last_page, first_page - 1, -1):
        for item in reversed(list(iterate_news(session, page))):
            item_data: Dict[str, Union[bool, Optional[str]]] = (
                item.to_json_dict()
            )
            item_url = item.get_page_url(categories)
            item_data['url'] = item_url
            if check_url and (item_url is not None):
                url_ok: bool = True
                try:
                    r1 = session.head(item_url)
                except requests.exceptions.RequestException:
                    url_ok = False
                else:
                    if r1.status_code != 200:
                        url_ok = False
                item_data['url_ok'] = url_ok
            data.append(item_data)

    json.dump(data, output_file, ensure_ascii=False, indent=4)


cli.add_command(process_categories)
cli.add_command(fetch_news)


if __name__ == '__main__':
    cli()
