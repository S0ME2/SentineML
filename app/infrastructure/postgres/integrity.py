from sqlalchemy.exc import IntegrityError

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"


def get_sqlstate(error: IntegrityError) -> str | None:
    return getattr(error.orig, "sqlstate", None)


def get_constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(error.orig, "diag", None)
    return getattr(diagnostic, "constraint_name", None)
