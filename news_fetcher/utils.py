"""Utilitary functions."""
import bs4


def html_to_wikitext(element: bs4.element.PageElement) -> str:
    """Convert HTML element to wiki-text recursively."""
    if isinstance(element, bs4.element.NavigableString):
        return str(element.string)
    if isinstance(element, bs4.element.Tag):
        content_str = ''.join(list(map(html_to_wikitext, element.children)))
        if element.name == 'a':
            href = element.attrs['href']
            return f'[{href} {content_str}]'
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
