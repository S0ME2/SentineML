from collections.abc import Callable

ErrorFactory = Callable[[str], Exception]


def required_text(value: object, field_name: str, error: ErrorFactory) -> str:
    if not isinstance(value, str):
        raise error(f"{field_name} must be a string")

    clean_value = value.strip()
    if not clean_value:
        raise error(f"{field_name} cannot be empty")

    return clean_value


def optional_text(
    value: object,
    field_name: str,
    error: ErrorFactory,
    *,
    strip: bool = False,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise error(f"{field_name} must be a string or null")

    return value.strip() if strip else value
