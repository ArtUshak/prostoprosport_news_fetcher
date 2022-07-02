"""Utilitary functions."""
import datetime
import time
from typing import Dict, List, Optional


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
    return check_str(data)


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
        check_str(key)
        check_str(value)
    return data


def check_list_str(data: object) -> List[str]:
    """Check if data is `List[str]` and return it."""
    if not isinstance(data, list):
        raise TypeError(data)
    for value in data:
        check_str(value)
    return data


def check_list_dict_str_object(data: object) -> List[Dict[str, object]]:
    """Check if data is `List[str]` and return it."""
    if not isinstance(data, list):
        raise TypeError(data)
    for value in data:
        check_dict_str_object(value)
    return data


def struct_time_to_datetime(value: time.struct_time) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(time.mktime(value))
