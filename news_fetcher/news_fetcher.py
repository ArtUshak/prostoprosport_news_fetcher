#!/usr/bin/env python3
"""Script to fetch news using API or RSS and convert them to wiki-text."""
import asyncio
import json
import pathlib
import re
import sys
from typing import Dict, Iterable, Optional, TextIO, Tuple

import aiohttp
import click
import tortoise
from tortoise.expressions import Q

import models
from db import init_db
from module import SourceModule
from prostoprosport import ProstoprosportModule
from rss import RSSModule
from utils import check_dict_str_object


def wrap_run(function):  # type: ignore
    async def wrapped(*args, **kwargs):  # type: ignore
        await init_db()
        try:
            result = await function(*args, **kwargs)
        finally:
            await tortoise.connection.connections.close_all(discard=True)
        return result

    return wrapped


def create_rss_module(
    data_file: Optional[TextIO], source_path: str,
    source_name: Optional[str]
) -> SourceModule:
    if (data_file is None) or (source_name is None):
        raise click.ClickException(
            '--data-file and --source-name are required when using '
            'RSS module'
        )
    try:
        return RSSModule(data_file, source_path, source_name)
    except ValueError as exc:
        raise click.ClickException(
            f'Error when initalizing RSS module: {exc}'
        )


def create_prostoprosport_module(
    data_file: Optional[TextIO], source_path: str,
    _source_name: Optional[str]
) -> SourceModule:
    try:
        return ProstoprosportModule(data_file, source_path)
    except ValueError as exc:
        raise click.ClickException(
            f'Error when initalizing Prostoprosport module: {exc}'
        )


DATA_CREATORS = {
    'rss': create_rss_module,
    'prostoprosport': create_prostoprosport_module
}


@click.group()
@click.pass_context
@click.option('--source-module', type=click.STRING, required=True)
@click.option('--data-file', type=click.File(mode='rt'))
@click.option('--source-path', type=click.STRING, required=True)
@click.option('--source-name', type=click.STRING)
def cli(
    ctx: click.Context, source_module: str,
    data_file: Optional[TextIO], source_path: str,
    source_name: str
) -> None:
    """Command line."""
    ctx.ensure_object(dict)

    if source_module not in DATA_CREATORS:
        raise click.ClickException(
            f'Invalid source module name {source_module}'
        )

    ctx.obj['MODULE'] = DATA_CREATORS[source_module](
        data_file, source_path, source_name
    )


async def fetch_news_async(
    module: SourceModule, first_page: int, last_page: int
) -> None:
    source, _ = await models.Source.get_or_create(
        slug_name=module.source_slug_name
    )

    async with aiohttp.ClientSession() as session:  # TODO: pool
        with click.progressbar(
            range(first_page, last_page + 1),
            length=(last_page + 1 - first_page)
        ) as bar1:
            for page in bar1:
                await module.insert_news(
                    session, page, source
                )


@click.command()
@click.pass_context
@click.option(
    '--first-page', type=click.IntRange(min=1), default=1,
    help='Number of first page to load, should be not less than 1'
)
@click.option(
    '--last-page', type=click.IntRange(min=1), default=1,
    help='Number of last page to load, should be not less than 1'
)
def fetch_news(
    ctx: click.Context, first_page: int, last_page: int
) -> None:
    """
    Fetch news from Prostoprosport.ru using API.

    Page numbers are from most recent (1) to least recent.
    Results are retrieved from least recent to first recent.
    """
    module = ctx.obj['MODULE']

    asyncio.run(
        wrap_run(fetch_news_async)(
            module, first_page, last_page
        )
    )


async def fetch_news_pages_async(module: ProstoprosportModule) -> None:
    source, _ = await models.Source.get_or_create(
        slug_name=module.source_slug_name
    )

    async with aiohttp.ClientSession() as session:
        articles = await source.articles.filter(
            Q(wikitext_paragraphs=None) & (
                Q(source_url_ok=1) | Q(source_url_ok=None)
            )
        )
        with click.progressbar(
            articles
        ) as bar:
            for article in bar:
                await module.check_url(article, session)
                await module.fetch_article(article, session)


@click.command()
@click.pass_context
def fetch_news_pages(
    ctx: click.Context
) -> None:
    """Fetch articles for news."""
    module = ctx.obj['MODULE']

    asyncio.run(wrap_run(fetch_news_pages_async)(module))


async def generate_wiki_pages_async(
    module: ProstoprosportModule, bot_name: str,
    output_directory_path: pathlib.Path
) -> Dict[str, Tuple[pathlib.Path, str, str]]:
    source, _ = await models.Source.get_or_create(
        slug_name=module.source_slug_name
    )

    pages: Dict[str, Tuple[pathlib.Path, str, str]] = {}

    with click.progressbar(
        await source.articles.filter(
            ~Q(wikitext_paragraphs=None) & Q(uploaded=False)
        )
    ) as bar:
        for article in bar:
            article_name = re.sub(r'[^0-9a-zA-Z\-_]+', '', article.slug_name)
            page_file_path = output_directory_path.joinpath(
                f'{article_name}.txt'
            )
            wiki_page_text = await module.get_wiki_page_text(article, bot_name)
            if wiki_page_text is not None:
                pages[article.title] = (
                    page_file_path, wiki_page_text, article.slug_name
                )

    return pages


@click.command()
@click.pass_context
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
    ctx: click.Context, output_file: TextIO, output_directory: str,
    bot_name: str
) -> None:
    """Generate wiki-pages for news articles."""
    module = ctx.obj['MODULE']

    pages = asyncio.run(wrap_run(generate_wiki_pages_async)(
        module, bot_name, pathlib.Path(output_directory)
    ))

    pages_data: Dict[str, Dict[str, str]] = {}
    with click.progressbar(pages.items(), length=len(pages)) as bar:
        for page_title, page_data in bar:
            page_file_path, wiki_page_text, page_slug_name = page_data
            with open(page_file_path, mode='wt') as page_file:
                page_file.write(wiki_page_text)
            pages_data[page_slug_name] = {
                'path': str(page_file_path),
                'title': page_title
            }

    json.dump(pages_data, output_file, ensure_ascii=False, indent=4)


async def mark_uploaded_pages_async(
    module: ProstoprosportModule, slug_names: Iterable[str]
) -> None:
    source, _ = await models.Source.get_or_create(
        slug_name=module.source_slug_name
    )

    await source.articles.filter(
        slug_name__in=slug_names
    ).update(
        uploaded=True
    )


@click.command()
@click.pass_context
@click.option(
    '--input-file', type=click.File(mode='rt'), required=True,
    help='Input list JSON file generated by `generate_wiki_pages`'
)
def mark_uploaded_pages(
    ctx: click.Context, input_file: TextIO
) -> None:
    """Mark news articles as uploaded."""
    module = ctx.obj['MODULE']

    pages_data = check_dict_str_object(json.load(input_file))

    asyncio.run(wrap_run(mark_uploaded_pages_async)(
        module,
        pages_data.keys()
    ))


cli.add_command(fetch_news)
cli.add_command(fetch_news_pages)
cli.add_command(generate_wiki_pages)
cli.add_command(mark_uploaded_pages)


if __name__ == '__main__':
    cli()
