from collections.abc import Callable

ErrorFactory = Callable[[str], Exception]


def required_text(
    value: object,
    field_name: str,
    error: ErrorFactory,
    *,
    max_length: int | None = None,
) -> str:
    if not isinstance(value, str):
        raise error(f"{field_name} must be a string")

    clean_value = value.strip()
    if not clean_value:
        raise error(f"{field_name} cannot be empty")
    if max_length is not None and len(clean_value) > max_length:
        raise error(f"{field_name} must be at most {max_length} characters")

    return clean_value


def optional_text(
    value: object,
    field_name: str,
    error: ErrorFactory,
    *,
    strip: bool = False,
    max_length: int | None = None,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise error(f"{field_name} must be a string or null")

    clean_value = value.strip() if strip else value
    if max_length is not None and len(clean_value) > max_length:
        raise error(f"{field_name} must be at most {max_length} characters")
    return clean_value
