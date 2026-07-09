def build_update_fields(field_values):
    return {
        column: value for column, value in field_values.items() if value is not None
    }


def require_found(resource, error):
    if resource is None:
        raise error

    return resource


def require_status(status, allowed_statuses, error):
    if status not in allowed_statuses:
        raise error
