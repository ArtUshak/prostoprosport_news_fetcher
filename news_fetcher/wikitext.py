"""Wikitext conversion functions."""
from typing import Callable

import bs4


def html_to_wikitext(
    element: bs4.element.PageElement, link_handler: Callable[[str], str],
    disable_bold_font: bool = False
) -> str:
    """Convert HTML element to wiki-text recursively."""
    if isinstance(element, bs4.element.NavigableString):
        return str(element.string)
    if isinstance(element, bs4.element.Tag):
        content_str = ''.join(list(map(
            lambda e:
            html_to_wikitext(
                e, link_handler, disable_bold_font=disable_bold_font
            ),
            element.children
        )))
        if element.name == 'a':
            href = element.attrs['href']
            try:
                url = link_handler(href)
            except ValueError:
                return content_str
            return f'[{url} {content_str}]'
        elif (element.name in ('b', 'strong')) and not disable_bold_font:
            return f"'''{content_str}'''"
        elif element.name == 'br':
            return '<br />'
        elif element.name in ('script', 'img'):
            return ''
        else:
            return content_str
    else:
        raise TypeError(element)
