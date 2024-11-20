from functools import cache
from typing import Any, Type, TypeVar

from pydantic import TypeAdapter

T = TypeVar("T")


@cache
def _get_type_adapter(type: Type[T]) -> TypeAdapter[T]:
    return TypeAdapter(type)


def check_type(obj: Any, type: Type[T]) -> T:
    adapter = _get_type_adapter(type)
    return adapter.validate_python(obj)  # type: ignore
