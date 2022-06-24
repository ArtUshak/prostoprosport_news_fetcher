"""Utilitary functions."""
import datetime
import time
from typing import Callable, Dict, List, Optional

import bs4


def check_str(data: object) -> str:
    """Check if data is `str` and return it."""
    if not isinstance(data, str):
        raise TypeError(data)
    return data


def check_int(data: object) -> int:
    """Check if data is `int` and return it."""
    if not isinstance(data, int):
        raise TypeError(data)
    return data


def check_optional_str(data: object) -> Optional[str]:
    """Check if data is `Optional[str]` and return it."""
    if data is None:
        return None
    if not isinstance(data, str):
        raise TypeError(data)
    return data


def check_bool(data: object) -> bool:
    """Check if data is `bool` and return it."""
    if not isinstance(data, bool):
        raise TypeError(data)
    return data


def check_dict_str_object(data: object) -> Dict[str, object]:
    """Check if data is `Dict[str, object]` and return it."""
    if not isinstance(data, dict):
        raise TypeError(data)
    return data


def check_dict_str_str(data: object) -> Dict[str, str]:
    """Check if data is `Dict[str, str]` and return it."""
    if not isinstance(data, dict):
        raise TypeError(data)
    for key, value in data.items():
        if not isinstance(key, str):
            raise TypeError(key)
        if not isinstance(value, str):
            raise TypeError(value)
    return data


def check_list_str(data: object) -> List[str]:
    """Check if data is `List[str]` and return it."""
    if not isinstance(data, list):
        raise TypeError(data)
    for value in data:
        if not isinstance(value, str):
            raise TypeError(value)
    return data


def html_to_wikitext(
    element: bs4.element.PageElement, link_handler: Callable[[str], str]
) -> str:
    """Convert HTML element to wiki-text recursively."""
    if isinstance(element, bs4.element.NavigableString):
        return str(element.string)
    if isinstance(element, bs4.element.Tag):
        content_str = ''.join(list(map(
            lambda e: html_to_wikitext(e, link_handler), element.children
        )))
        if element.name == 'a':
            href = element.attrs['href']
            try:
                url = link_handler(href)
            except ValueError:
                return content_str
            return f'[{url} {content_str}]'
        elif element.name in ('a', 'strong'):
            return f"'''{content_str}'''"
        elif element.name == 'br':
            return '<br />'
        elif element.name in ('script', 'img'):
            return ''
        else:
            return content_str
    else:
        raise TypeError(element)


def struct_time_to_datetime(value: time.struct_time) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(time.mktime(value))
